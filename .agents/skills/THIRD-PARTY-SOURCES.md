# Imported agent skills

These skills are separate from EVKey Linux Community's GPL-3.0-or-later source. Preserve each upstream notice and hash in `skills-lock.json` when updating them.

- `bash-defensive-patterns` and `python-testing-patterns`: [wshobson/agents](https://github.com/wshobson/agents), MIT; full upstream terms are in [WSHOBSON-MIT-LICENSE](WSHOBSON-MIT-LICENSE).
- `python-executor`: [inference-sh/skills](https://github.com/inference-sh/skills), MIT as declared in upstream `.claude-plugin/plugin.json`. Registry review flags external installs, arbitrary network-capable Python execution, and broad `Bash(belt *)`; see [AGENTS.md](../../AGENTS.md) before use.
- `archify`: [tt-a1i/archify](https://github.com/tt-a1i/archify), MIT; imported from immutable commit `2ab3cae7ac2c2a55d7386ca789d03c4fcd31816c` (release tag object `679f195584e4216fd582c073d8964b3a9f59107e`, v3.0.1; official archive SHA-256 `b0b23bd28db314f04ca8ab9620fe20f8c1ac6474a3546bd8fe4679508aa1b7f5`). Full upstream terms are in [ARCHIFY-MIT-LICENSE](ARCHIFY-MIT-LICENSE); bundled third-party assets retain their separate notices.
- AutoSkills installer itself is CC BY-NC 4.0; installer code is not included here. Use each selected skill under its actual upstream source license, not the installer license or project GPL by assumption.
