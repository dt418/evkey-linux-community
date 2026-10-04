# Contributing

EVKey Linux Community is an independent community project based on Fcitx5 Lotus and Bamboo source. Preserve upstream licenses, copyright notices, and attribution when changing or redistributing source.

**This community edition is inspired by EVKey and uses Lotus/Bamboo; it is not the official EVKey release.**

## Build and test

See dependencies and build commands in [README.en.md](README.en.md). Use a separate build directory:

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Engine/helper changes require testing in a real Fcitx5 Linux session. Unit tests and successful builds do not replace direct typing checks. Do not expand helper privileges or grant keyboard-device read access without an approved security design.

## Changes

- Keep scope small; support CMake 3.16, C++17, and Go 1.18.
- Update docs and observable-behavior tests when contracts change.
- Do not log tokens, typed content, or user-identifying data.
- Do not add release, package-signing, or artifact-publishing workflows.
- State environment and commands run in pull requests; do not claim desktop verification unless performed.

## Bug reports

Include distro/version, Fcitx5 version, input mode, reproduction steps, and logs with sensitive data removed. Do not send typed text or personal information.
