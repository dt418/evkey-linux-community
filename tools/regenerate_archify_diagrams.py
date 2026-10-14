#!/usr/bin/env python3
"""Finalize approved contributor Archify diagrams without publishing them to Pages."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import re
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .check_archify_artifacts import (
        ARCHIFY_COMMIT,
        EXPECTED_PAIRS,
        SOURCE_REPOSITORY,
        SOURCE_REVISION,
        contained_archify_path,
    )
else:
    from check_archify_artifacts import (
        ARCHIFY_COMMIT,
        EXPECTED_PAIRS,
        SOURCE_REPOSITORY,
        SOURCE_REVISION,
        contained_archify_path,
    )

CLI_RELATIVE = Path(".agents/skills/archify/bin/archify.mjs")
REQUIRED_GATES = {"validate", "deliver", "check", "browser-check"}
ROW_KEYS = {
    "type",
    "locale",
    "candidate",
    "generated",
    "candidate_sha256",
    "generated_sha256",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def contained(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or "\\" in value:
        raise ValueError(f"invalid repository-relative artifact path: {value!r}")
    path = (root / value).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"artifact path escapes repository root: {value!r}") from error
    return path


def load_manifest(root: Path) -> tuple[dict[str, Any], Path]:
    path = contained_archify_path(root, ".archify/diagram-manifest.json", "manifest")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise ValueError("manifest must use version 1")
    if manifest.get("archify_commit") != ARCHIFY_COMMIT or manifest.get("source_revision") != SOURCE_REVISION:
        raise ValueError("manifest must pin approved Archify and source revisions")
    rows = manifest.get("artifacts")
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError("manifest must contain exactly four artifact rows")
    pairs = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise ValueError("manifest artifact row has invalid fields")
        pair = (row.get("type"), row.get("locale"))
        if pair not in EXPECTED_PAIRS or pair in pairs:
            raise ValueError(f"unexpected or duplicate artifact pair: {pair!r}")
        pairs.add(pair)
        candidate = contained_archify_path(root, row["candidate"], "candidate")
        generated = contained_archify_path(root, row["generated"], "generated")
        candidate_data = json.loads(candidate.read_text(encoding="utf-8"))
        meta = candidate_data.get("meta", {}) if isinstance(candidate_data, dict) else {}
        repository = meta.get("repository") if isinstance(meta, dict) else None
        slug = "runtime-architecture" if row["type"] == "architecture" else "input-modes"
        candidate_parent = Path(row["candidate"]).parent.as_posix()
        if (not re.fullmatch(rf"\.archify/{row['type']}-{slug}-\d{{8}}-\d{{6}}", candidate_parent)
                or row["candidate"] != f"{candidate_parent}/candidate.json"
                or row["generated"] != f"{candidate_parent}/{slug}.html"):
            raise ValueError(f"artifact paths disagree with contributor-only layout: {row!r}")
        if (candidate_data.get("diagram_type") != row["type"] or meta.get("locale") != row["locale"]
                or meta.get("output") != row["generated"] or meta.get("quality_profile") != "showcase"
                or not isinstance(repository, dict) or repository.get("url") != SOURCE_REPOSITORY
                or repository.get("revision") != SOURCE_REVISION or repository.get("link_mode") != "local-only"):
            raise ValueError(f"candidate metadata disagrees with manifest: {row['candidate']}")
        if not candidate.is_file() or not generated.parent.is_dir():
            raise ValueError(f"candidate or generated destination folder missing: {row['candidate']} / {row['generated']}")
    if pairs != EXPECTED_PAIRS:
        raise ValueError("manifest does not include every approved type/locale pair")
    return manifest, path


def _receipt_from(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(receipt, dict) and receipt.get("command") == "finalize":
            return receipt
    raise ValueError("Archify finalize did not return a JSON finalize receipt")


def finalize(root: Path, row: dict[str, Any], cli: Path) -> dict[str, Any]:
    candidate = contained_archify_path(root, row["candidate"], "candidate")
    output = contained_archify_path(root, row["generated"], "generated")
    candidate_hash = digest(candidate)
    command = [
        "node", str(cli), "finalize", row["type"], str(candidate), str(output),
        "--repo-root", str(root), "--quality", "showcase", "--json",
    ]
    env = os.environ.copy()
    env["ARCHIFY_UPDATE_CHECK_DISABLED"] = "1"
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError(f"finalize failed for {row['candidate']} (exit {result.returncode})")
    receipt = _receipt_from(result.stdout)
    if receipt.get("ok") is not True or receipt.get("status") != "pass":
        raise RuntimeError(f"finalize receipt failed for {row['candidate']}")
    gates = receipt.get("gates")
    if not isinstance(gates, dict) or set(gates) != REQUIRED_GATES or any(gates.get(gate) != "pass" for gate in REQUIRED_GATES):
        raise RuntimeError(f"finalize receipt lacks passing validation/provenance/browser gates for {row['candidate']}")
    if digest(candidate) != candidate_hash:
        raise RuntimeError(f"candidate changed during finalize: {row['candidate']}")
    return receipt


def write_sums(path: Path, pairs: list[tuple[str, Path]], root: Path) -> None:
    lines = [f"{digest_value}  {artifact.relative_to(root).as_posix()}\n" for digest_value, artifact in pairs]
    path.write_text("".join(lines), encoding="utf-8", newline="\n")


def prepare_vietnamese_candidates(root: Path, manifest: dict[str, Any]) -> None:
    catalog_path = contained_archify_path(root, ".archify/translations/vi.json", "translation catalog")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not all(isinstance(value, str) and value for value in catalog.values()):
        raise ValueError("Vietnamese translation catalog must map canonical keys to non-empty strings")
    script = (
        "import fs from 'node:fs'; "
        "import { validateTranslations } from './.agents/skills/archify/renderers/shared/i18n.mjs'; "
        "const catalog=JSON.parse(fs.readFileSync('.archify/translations/vi.json','utf8')); "
        "const result=validateTranslations(catalog); "
        "console.log(JSON.stringify(result)); "
        "if(result.coverage!==1||result.missingKeys.length||result.unknownKeys.length||result.placeholderMismatches.length) process.exit(1);"
    )
    validation = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if validation.returncode != 0:
        raise ValueError(f"Vietnamese catalog key/placeholder validation failed: {validation.stdout}{validation.stderr}")
    print(f"Vietnamese catalog verified: {validation.stdout.strip()}")

    for row in manifest["artifacts"]:
        if row.get("locale") != "vi":
            continue
        candidate_path = contained_archify_path(root, row["candidate"], "candidate")
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        meta = candidate.get("meta") if isinstance(candidate, dict) else None
        if not isinstance(meta, dict) or meta.get("locale") != "vi":
            raise ValueError(f"Vietnamese candidate metadata is invalid: {row['candidate']}")
        meta["translations"] = catalog
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )


def regenerate(root: Path) -> list[dict[str, Any]]:
    root = root.resolve(strict=True)
    manifest, manifest_path = load_manifest(root)
    prepare_vietnamese_candidates(root, manifest)
    cli = contained(root, CLI_RELATIVE.as_posix())
    if not cli.is_file():
        raise ValueError(f"pinned Archify CLI missing: {cli}")
    receipts = [finalize(root, row, cli) for row in manifest["artifacts"]]

    candidate_outputs: list[tuple[str, Path]] = []
    for row in manifest["artifacts"]:
        candidate = contained_archify_path(root, row["candidate"], "candidate")
        generated = contained_archify_path(root, row["generated"], "generated")
        if not generated.is_file():
            raise ValueError(f"finalize produced no HTML: {row['generated']}")
        row["candidate_sha256"] = digest(candidate)
        row["generated_sha256"] = digest(generated)
        candidate_outputs.extend(((row["candidate_sha256"], candidate), (row["generated_sha256"], generated)))

    sums_path = contained_archify_path(root, ".archify/SHA256SUMS", "checksum file")
    write_sums(sums_path, candidate_outputs, root)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)")
    args = parser.parse_args()
    try:
        receipts = regenerate(args.root)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Archify regeneration failed: {error}", file=sys.stderr)
        return 1
    print(f"Regenerated {len(receipts)} contributor diagrams after all four finalizer gates passed per diagram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
