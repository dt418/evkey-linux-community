---
name: evkey-packaging
description: Implement or review EVKey Linux Community packaging, distro recipes, optional uinput-helper split, service/udev install metadata, CI release artifacts, source archives, or checksums. Use whenever changing `packaging/`, `debian/`, `misc/`, Nix files, or package workflow jobs.
---

# EVKey packaging

Package `fcitx5-evkey` for Linux glibc x86_64 with optional `fcitx5-evkey-uinput`. Main package must deliver Preedit/Fake Backspace without privileged helper; helper package is explicit opt-in Smooth transport.

## Procedure

1. Read project-local upstream `systematic-debugging` before diagnosing an unknown packaging failure and `test-driven-development` before adding executable package behavior. Read `docs/development.md` for canonical build/package commands and artifact contract. Read root `CMakeLists.txt`, `misc/CMakeLists.txt`, `server/CMakeLists.txt`, affected recipe, and `.github/workflows/build.yml`. Inspect matching staged install components before changing file lists. **Done:** every installed file traces to build/install source and exactly one package.

2. Preserve package split. Main package owns addon `libevkey.so`, input-method/addon metadata, settings UI, dictionaries, icons, translations, and licenses. `fcitx5-evkey-uinput` owns `fcitx5-evkey-server`, systemd service, sysusers file, udev rules, and module-load metadata. Helper depends on matching main version; main must not depend or recommend helper. **Done:** installing main alone needs no system account, ACL, udev rule, helper service, or elevated privilege.

3. Keep helper opt-in and least privilege. `fcitx5-evkey-server@.service` runs only `--uid %i` as `evkey-input`, keeps systemd sandboxing and empty capability sets, and is never enabled automatically. Retain narrow udev ACL intent: rw only for `/dev/uinput`; read only for `seat0` pointer/touch devices excluding keyboards. Package scripts may reload metadata and print activation guidance, but must not enable instances, alter desktop-user groups, or loosen permissions. **Done:** recipe changes preserve dedicated account, no raw keyboard ACL, no `input` group access, and no privilege escalation.

4. Match each distro convention without copying release claims. Update paired Debian files under `packaging/debian/` and staged `debian/` only when required by project workflow; Fedora uses `packaging/rpm/fedora/fcitx5-evkey.spec`; Arch uses `packaging/arch/PKGBUILD`; Nix uses `packaging/nix/`. Keep dependencies derived from actual CMake/Python/ELF requirements and preserve CMake >= 3.16, Fcitx5 >= 5.1.7, and Go >= 1.18 source contract. **Done:** package metadata names real files/dependencies and no recipe points at Lotus artifacts or fake repositories.

5. Publish traceable artifacts only. CI source job creates versioned corresponding source archive and `SHA256SUMS`; distro jobs package from that source and emit per-artifact checksums. Do not publish, sign, advertise remote repository, or record checksum until source archive and computed checksum exist. Treat source-tree build as build evidence only; validate installed package behavior from package-installed paths before calling addon/UI integration proven. **Done:** release artifact, source, checksum, and package provenance agree.

6. For one changed executable package contract, follow upstream `test-driven-development`: make focused metadata/script/CI coverage red at an existing seam, make it green, then run installed-package smoke from `docs/development.md`. Do not claim legacy recipes were developed TDD. Package helper/service tests and headless/socket tests prove package metadata or protocol boundaries, not uinput injection, logind, or native Wayland/X11. **Done:** changed artifact boundary has red-to-green focused coverage and installed-package smoke evidence, with native evidence clearly separated.

## Guardrails

- Do not add curl-pipe-shell installers, global tool configuration, secrets, signing keys, or hardcoded workstation paths.
- Do not make helper mandatory, auto-started, or silently enabled during install/upgrade.
- Do not use tests/mocks to claim real kernel device, active-session, or desktop compatibility.
- Removal must preserve user configuration and unrelated IME/software; remove only helper-managed ACLs/services when applicable.

## Stop

Stop when recipe, CMake install components, lifecycle policy, CI source/artifact/checksum flow, and package split describe same deliverable, with red-to-green coverage for changed executable contract. Use `docs/development.md` for exact commands and expected artifact inspection; do not duplicate command tables here.
