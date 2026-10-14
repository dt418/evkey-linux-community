#!/usr/bin/env python3
"""Verify contributor Archify candidates, generated HTML, and provenance checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ARCHIFY_COMMIT = "2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c"
SOURCE_REPOSITORY = "git@github.com:dt418/evkey-linux-community.git"
SOURCE_REVISION = "87e6de6e59b96310876450a723e3b9ce5d613d41"
EXPECTED_PAIRS = {
    ("architecture", "en"),
    ("architecture", "vi"),
    ("workflow", "en"),
    ("workflow", "vi"),
}
ROW_KEYS = {
    "type",
    "locale",
    "candidate",
    "generated",
    "candidate_sha256",
    "generated_sha256",
}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _contained_path(root: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty relative path")
    relative = Path(value)
    if relative.is_absolute() or "\\" in value:
        raise ValueError(f"{field} must be a repository-relative POSIX path: {value!r}")
    target = (root / relative).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{field} escapes repository root: {value!r}") from error
    return target


def _archify_root(root: Path) -> Path:
    path = root / ".archify"
    if path.is_symlink() or not path.is_dir():
        raise ValueError(".archify must be a real repository directory")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ValueError(".archify must not resolve through a symlink")
    return resolved


def contained_archify_path(root: Path, value: Any, field: str) -> Path:
    target = _contained_path(root, value, field)
    try:
        target.relative_to(_archify_root(root))
    except ValueError as error:
        raise ValueError(f"{field} resolves outside .archify: {value!r}") from error
    return target


def _read_sums(path: Path, root: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"missing checksum file: {path.relative_to(root)}")
    entries: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"invalid checksum row at {path.relative_to(root)}:{number}")
        digest, name = match.groups()
        if name in entries:
            raise ValueError(f"duplicate checksum path in {path.relative_to(root)}: {name}")
        entries[name] = digest
    return entries


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_manifest(root: Path) -> None:
    """Verify contributor Archify candidates, generated artifacts, hashes, and provenance."""
    root = root.resolve(strict=True)
    manifest_path = contained_archify_path(root, ".archify/diagram-manifest.json", "manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read manifest: {error}") from error
    if not isinstance(manifest, dict) or set(manifest) != {"version", "archify_commit", "source_revision", "artifacts"}:
        raise ValueError("manifest must contain only version, archify_commit, source_revision, and artifacts")
    if manifest["version"] != 1 or manifest["archify_commit"] != ARCHIFY_COMMIT:
        raise ValueError("manifest version or pinned Archify commit is incorrect")
    if manifest["source_revision"] != SOURCE_REVISION:
        raise ValueError("manifest source revision is not the approved committed snapshot")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != len(EXPECTED_PAIRS):
        raise ValueError("manifest must contain exactly four artifacts")

    pairs: set[tuple[str, str]] = set()
    candidates_and_generated: dict[str, str] = {}
    for index, row in enumerate(artifacts):
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise ValueError(f"artifact row {index} has invalid fields")
        pair = (row["type"], row["locale"])
        if pair not in EXPECTED_PAIRS or pair in pairs:
            raise ValueError(f"unexpected or duplicate artifact type/locale: {pair!r}")
        pairs.add(pair)

        paths = {
            key: contained_archify_path(root, row[key], f"artifact[{index}].{key}")
            for key in ("candidate", "generated")
        }
        candidate_sha = row["candidate_sha256"]
        generated_sha = row["generated_sha256"]
        if any(not isinstance(value, str) or not HASH_RE.fullmatch(value) for value in (candidate_sha, generated_sha)):
            raise ValueError(f"artifact row {index} contains an invalid SHA-256")
        for key, path in paths.items():
            if not path.is_file():
                raise ValueError(f"missing {key} artifact: {row[key]}")

        try:
            candidate = json.loads(paths["candidate"].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot read candidate {row['candidate']}: {error}") from error
        if not isinstance(candidate, dict) or candidate.get("diagram_type") != row["type"]:
            raise ValueError(f"candidate type disagrees with manifest: {row['candidate']}")
        slug = "runtime-architecture" if row["type"] == "architecture" else "input-modes"
        candidate_parent = Path(row["candidate"]).parent.as_posix()
        if (not re.fullmatch(rf"\.archify/{row['type']}-{slug}-\d{{8}}-\d{{6}}", candidate_parent)
                or row["candidate"] != f"{candidate_parent}/candidate.json"
                or row["generated"] != f"{candidate_parent}/{slug}.html"):
            raise ValueError(f"artifact paths disagree with the contributor-only layout: {row!r}")
        meta = candidate.get("meta")
        if (not isinstance(meta, dict) or meta.get("locale") != row["locale"]
                or meta.get("output") != row["generated"] or meta.get("quality_profile") != "showcase"):
            raise ValueError(f"candidate locale/output/quality disagrees with manifest: {row['candidate']}")
        repository = meta.get("repository")
        if (
            not isinstance(repository, dict)
            or repository.get("url") != SOURCE_REPOSITORY
            or repository.get("revision") != SOURCE_REVISION
            or repository.get("link_mode") != "local-only"
        ):
            raise ValueError(f"candidate repository identity disagrees with manifest: {row['candidate']}")

        for key, path, digest in (
            ("candidate", paths["candidate"], candidate_sha),
            ("generated", paths["generated"], generated_sha),
        ):
            actual = _digest(path)
            if actual != digest:
                raise ValueError(f"{key} hash mismatch for {row[key]}")
        candidates_and_generated[row["candidate"]] = candidate_sha
        candidates_and_generated[row["generated"]] = generated_sha

    if pairs != EXPECTED_PAIRS:
        raise ValueError("manifest does not contain every approved type/locale pair")
    project_sums = _read_sums(contained_archify_path(root, ".archify/SHA256SUMS", "project checksum file"), root)
    if project_sums != candidates_and_generated:
        raise ValueError(".archify/SHA256SUMS does not exactly cover manifest candidates and generated HTML")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)")
    args = parser.parse_args()
    try:
        check_manifest(args.root)
    except (OSError, ValueError) as error:
        print(f"Archify artifact check failed: {error}", file=sys.stderr)
        return 1
    print("Contributor Archify manifest and checksums agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
