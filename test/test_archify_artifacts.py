import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import regenerate_archify_diagrams
from tools.check_archify_artifacts import check_manifest

ARCHIFY_COMMIT = "2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c"
SOURCE_REPOSITORY = "git@github.com:dt418/evkey-linux-community.git"
SOURCE_REVISION = "87e6de6e59b96310876450a723e3b9ce5d613d41"
PAIRS = (("architecture", "en"), ("architecture", "vi"), ("workflow", "en"), ("workflow", "vi"))


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class ArchifyArtifactsTest(unittest.TestCase):
    def make_repository(self, root: Path) -> dict:
        rows = []
        sums = []
        for diagram_type, locale in PAIRS:
            slug = "runtime-architecture" if diagram_type == "architecture" else "input-modes"
            timestamp = "20261005-021646" if locale == "en" else "20261005-022041"
            stem = f"{diagram_type}-{slug}-{timestamp}"
            candidate_path = f".archify/{stem}/candidate.json"
            generated_path = f".archify/{stem}/{slug}.html"
            candidate = {
                "schema_version": 1 if diagram_type == "architecture" else 2,
                "diagram_type": diagram_type,
                "meta": {
                    "locale": locale,
                    "output": generated_path,
                    "quality_profile": "showcase",
                    "repository": {
                        "url": SOURCE_REPOSITORY,
                        "revision": SOURCE_REVISION,
                        "link_mode": "local-only",
                    },
                },
            }
            candidate_bytes = json.dumps(candidate).encode()
            html = f"<html lang='{locale}'>{diagram_type}</html>".encode()
            for path, content in ((candidate_path, candidate_bytes), (generated_path, html)):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            row = {
                "type": diagram_type,
                "locale": locale,
                "candidate": candidate_path,
                "generated": generated_path,
                "candidate_sha256": sha256(candidate_bytes),
                "generated_sha256": sha256(html),
            }
            rows.append(row)
            sums.extend(((row["candidate_sha256"], candidate_path), (row["generated_sha256"], generated_path)))

        manifest = {
            "version": 1,
            "archify_commit": ARCHIFY_COMMIT,
            "source_revision": SOURCE_REVISION,
            "artifacts": rows,
        }
        (root / ".archify/diagram-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (root / ".archify/SHA256SUMS").write_text("".join(f"{digest}  {path}\n" for digest, path in sums), encoding="utf-8")
        return manifest

    def test_candidate_and_generated_diagrams_pass_without_public_site_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_repository(Path(directory))
            check_manifest(Path(directory))

    def test_changed_generated_html_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_repository(root)
            (root / manifest["artifacts"][0]["generated"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "generated hash mismatch"):
                check_manifest(root)

    def test_missing_candidate_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_repository(root)
            (root / manifest["artifacts"][0]["candidate"]).unlink()
            with self.assertRaisesRegex(ValueError, "missing candidate artifact"):
                check_manifest(root)

    def test_path_traversal_outside_root_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_repository(root)
            manifest["artifacts"][0]["candidate"] = "../outside.json"
            (root / ".archify/diagram-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes repository root"):
                check_manifest(root)

    def test_manifest_rejects_publication_copy_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_repository(root)
            manifest["artifacts"][0]["published"] = "site/diagrams/en/runtime-architecture.html"
            (root / ".archify/diagram-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid fields"):
                check_manifest(root)

    def test_symlinked_artifact_directory_cannot_publish_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_repository(root)
            artifact_dir = root / Path(manifest["artifacts"][0]["candidate"]).parent
            target_dir = root / "site" / artifact_dir.name
            target_dir.mkdir(parents=True)
            for name in ("candidate.json", "runtime-architecture.html"):
                (target_dir / name).write_bytes((artifact_dir / name).read_bytes())
            backup = root / ".archify" / "saved" / artifact_dir.name
            backup.parent.mkdir()
            artifact_dir.rename(backup)
            try:
                artifact_dir.symlink_to(target_dir, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "outside .archify"):
                check_manifest(root)

    def test_invalid_manifest_is_rejected_before_candidate_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_repository(root)
            catalog_path = root / ".archify" / "translations" / "vi.json"
            catalog_path.parent.mkdir(parents=True)
            catalog_path.write_text(json.dumps({"greeting": "xin chào"}), encoding="utf-8")
            unrelated_path = root / ".archify" / "unrelated.json"
            unrelated = {
                "diagram_type": "architecture",
                "meta": {
                    "locale": "vi",
                    "translations": {"sentinel": "unchanged"},
                },
            }
            unrelated_path.write_text(json.dumps(unrelated), encoding="utf-8")
            manifest["artifacts"][1]["candidate"] = ".archify/unrelated.json"
            (root / ".archify/diagram-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            original = unrelated_path.read_bytes()
            validation = SimpleNamespace(
                returncode=0,
                stdout='{"coverage":1,"missingKeys":[],"unknownKeys":[],"placeholderMismatches":[]}',
                stderr="",
            )

            with patch.object(regenerate_archify_diagrams.subprocess, "run", return_value=validation):
                with self.assertRaisesRegex(ValueError, "artifact paths"):
                    regenerate_archify_diagrams.regenerate(root)
            self.assertEqual(unrelated_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
