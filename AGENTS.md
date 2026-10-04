# Working on EVKey Linux Community

Independent community edition inspired by EVKey, derived from licensed Lotus/Bamboo. This is a native Linux input method, not an official EVKey port or a web app. Preserve copyright, licenses and attribution.

## Start here

- Read [CONTEXT.md](CONTEXT.md) for domain vocabulary.
- Read [docs/development.md](docs/development.md) for source ownership, prerequisites, harness commands and verification levels.
- At task start, use project-pinned Superpowers workflow in `.agents/skills/using-superpowers/`; use only skills relevant to task. Project requirements and safety rules override generic workflows.
- Unknown or intermittent bug: read `systematic-debugging` before changing code. Feature or bug fix: read `test-driven-development`; for each observable behavior, prove focused test fails for intended reason, make minimum fix, prove same test passes, then run real surface smoke.
- Use repository skills when changing their area:
  - Input modes, composition, focus, replacement or helper protocol: [.agents/skills/evkey-engine/SKILL.md](.agents/skills/evkey-engine/SKILL.md).
  - Qt Settings, drafts, D-Bus recovery, layouts or translations: [.agents/skills/evkey-settings/SKILL.md](.agents/skills/evkey-settings/SKILL.md).
  - Package recipes, runtime/helper split or release artifacts: [.agents/skills/evkey-packaging/SKILL.md](.agents/skills/evkey-packaging/SKILL.md).

## Invariants

- Compile and run Linux code on Linux. Windows hosts may use WSL; WSLg does not prove native Wayland or hardware Uinput behavior.
- Keep CMake 3.16, C++17, Go 1.18 and Fcitx5 5.1.7 compatibility. Retain the legacy/modern Fcitx API branches.
- Public namespace is `fcitx5-evkey` / `evkey`; private `Lotus*` names and upstream attributions remain intentional.
- Requested mode and effective mode differ during fallback. Keep composition, replacement and cancellation owned by the original input context and generation.
- Sensitive/disabled contexts bypass transformations. Logs contain operational errors, never typed content or macro expansion.
- AutoSkills adds generic Bash/Python skills; this project is primarily C++/Go, and the detector has no coverage for those languages. Keep engine and packaging tasks on the project-specific skills.
- `python-executor` is third-party and review-flagged. Never send project source, config, credentials, tests, user input, or other private data to `belt`/inference.sh; do not execute remote code there unless user explicitly requests that specific external service.
- Settings changes remain drafts until saved. Keep drafts on read/write failure and reconnect; merge with latest backend values. Do not replay ambiguous writes.
- Reuse backend options and existing editors. Each setting has one owner; no parallel config store or invented EVKey-only behavior.

## Change and prove

1. Reproduce observable behavior and trace the responsible code before editing. Preserve unrelated local changes.
2. Patch the owning layer; keep meaningful behavior regressions, not source-text or mock-forwarding assertions.
3. Run the relevant harness gate, then exercise the changed surface. Native UI changes need a visible window; transport changes need actual application input in addition to headless tests.
4. Update affected docs/translations/contracts. Report commands, environment and results separately from unverified desktop or hardware claims.
5. Stage source deliberately. Build trees, `debian/` staging, caches, credentials and `dist/` artifacts stay out of Git. Publish packages manually with corresponding source and checksums; do not add automatic signing/publishing or enable helper services.

Completion means the requested behavior is exercised, affected callers are updated, and remaining environment limits are explicit. A green build alone is not native compatibility evidence.

## Agent workflows

- Upstream [Superpowers](https://github.com/obra/superpowers) skills for Codex and Claude Code are project-local and pinned by `skills-lock.json`. Source is `.agents/skills/`; Claude Code copies live in `.claude/skills/`. `using-superpowers` selects applicable process skills; `test-driven-development` requires red → green for new observable behavior, and `systematic-debugging` precedes fixes for unexplained failures.
- Skills do not override project safety, user intent, acceptance criteria or evidence. Upstream brainstorm/plan workflows help with genuinely open-ended features; do not ask for approval when requirements are already explicit.
- Custom `evkey-engine`, `evkey-settings` and `evkey-packaging` skills pair those workflows with domain-specific contracts. Load the relevant skill before touching those subsystems.
- Review skill changes against the pinned source; do not run an upstream skill authoring evaluation for product skills unless the user requests one.
