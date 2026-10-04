# Contributing

EVKey Linux Community is an independent community project based on Fcitx5 Lotus and Bamboo source. Preserve upstream licenses, copyright notices, and attribution when changing or redistributing source.

**This community edition is inspired by EVKey and uses Lotus/Bamboo; it is not the official EVKey release.**

## Build and test

See [README.en.md](README.en.md) for dependencies. The shared CMake, Go, Settings, and D-Bus harness lives in [docs/development.md](docs/development.md):

```sh
tools/dev.sh help
tools/dev.sh check
tools/dev.sh settings
tools/dev.sh dbus
```

Engine/helper changes require testing in a real Fcitx5 Linux session. Unit tests and successful builds do not replace direct typing checks. Do not expand helper privileges or grant keyboard-device read access without an approved security design.

## Changes

- Keep scope small; support CMake 3.16, C++17, and Go 1.18.
- Use test-driven development for behavior changes: prove an existing behavior seam fails for the intended reason, make the smallest fix, rerun that test, then smoke the actual surface. Headless and mocked tests do not prove desktop/hardware compatibility.
- Superpowers and project skills for engine, Settings, and packaging live in `.agents/skills/`; `skills-lock.json` pins upstream.
- Do not add automatic release, package-signing, or artifact-publishing workflows.
- State environment and commands run in pull requests; do not claim desktop verification unless performed.

## Bug reports

Include distro/version, Fcitx5 version, input mode, reproduction steps, and logs with sensitive data removed. Do not send typed text or personal information.
