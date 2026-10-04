# EVKey Linux Community

Vietnamese input method for Fcitx5 on Linux, based on Fcitx5 Lotus and Bamboo source. Independent community project.

**This community edition is inspired by EVKey and uses Lotus/Bamboo; it is not the official EVKey release.** It is not affiliated with, endorsed by, or distributed by EVKey's author.

## Modes

- **Preedit** — show composition before commit; no privileged helper.
- **Fake Backspace** — replace text using application backspace events; no privileged helper.
- **Uinput (Smooth)** — optional mode provided by `fcitx5-evkey-uinput`. If helper rejects a request or is unavailable, engine falls back to Preedit. Helper does not read keyboard devices.

Inherited engine sources expose `Telex`, `VNI`, `Telex + VNI`, `Telex + VNI + VIQR`, `VIQR`, `Microsoft layout`, `VNI French keyboard`, and `Custom`. VIQR accepts both `+` and `*` for `ư/ơ`, matching X-Unikey's VIQR* keystroke behavior without a duplicate menu entry. Output charsets include Unicode, TCVN3 (ABC), VNI Windows, decomposed Unicode, Windows 1258, VIQR, VISCII, VPS, BKHCM 1/2, Vietware X/Full, UTF-8, decimal/hex NCR, and hexadecimal/decimal Unicode C strings. Settings displays every choice the engine backend provides.

## System tray and quick switching

The EVKey status menu in Fcitx5 provides **Settings**, **Input Method**, and **Charset** actions. Use **Input Method** or **Charset** to change and save selections without opening the settings window. Settings also exposes both selectors.

## Build

Debian/Ubuntu dependencies:

```sh
sudo apt install cmake extra-cmake-modules g++ golang pkg-config \
  fcitx5-modules-dev libfcitx5core-dev libfcitx5config-dev \
  libfcitx5utils-dev libinput-dev libudev-dev libsystemd-dev gettext \
  python3-qtpy python3-dbus acl librsvg2-bin
```

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Install components separately:

```sh
sudo cmake --install build --component Runtime
sudo cmake --install build --component Uinput  # optional privileged helper
```

Other distro package recipes are in `packaging/`. Arch recipe expects a release archive and SHA-256 supplied through its documented makepkg variables; it does not download unverified source.

## Development and agents

Developer prerequisites, source map, Linux harness, and native smoke procedures: [docs/development.md](docs/development.md). Contribution workflow: [CONTRIBUTING.en.md](CONTRIBUTING.en.md).

`AGENTS.md` and `CONTEXT.md` describe repository rules and shared vocabulary. Pinned Superpowers plus engine, Settings, and packaging skills are project-local under `.agents/skills/`; no global agent setup is required.

## NixOS

`flake.nix` exports `packages.<system>.default` and `nixosModules.default`. Import the module into your NixOS configuration and set `programs.fcitx5-evkey.enable = true;`. The main package installs runtime only. `programs.fcitx5-evkey.uinput.enable = true;` adds the optional helper output, account, systemd unit, kernel module, and udev rules; it does not start the service automatically. Start `fcitx5-evkey-server@<UID>.service` only while that UID has an active desktop session.

## Security boundary

Runtime component and distro main packages omit helper executable, account, udev rules, and service. CMake install without `--component` installs all components; use Runtime-only if Smooth is not needed. Installing Uinput does not enable its service. Optional helper runs as dedicated `evkey-input` account. It checks Unix peer credentials, active unlocked logind session, caller UID, and protocol framing; it does not read keyboard devices or inspect `/proc` command lines. Udev grants helper access only to `/dev/uinput` and eligible non-keyboard pointing devices. Review local distro/systemd/udev policy before enabling it.

## License and attribution

Project distributed under GPL-3.0-or-later; see `LICENSE`. Imported Fcitx5 Lotus and Bamboo sources retain upstream copyright and notices. `bamboo/bamboo-core` carries its own license. Preserve attribution when redistributing.

Agent-workflow licenses remain separate: upstream Superpowers skills include their MIT notice in `.agents/skills/SUPERPOWERS-LICENSE`; AutoSkills skill sources and licenses are documented in [.agents/skills/THIRD-PARTY-SOURCES.md](.agents/skills/THIRD-PARTY-SOURCES.md), not covered by this project's GPL license. `python-executor` sends arbitrary Python to an external service; do not send private project data to inference.sh without explicit user approval.
