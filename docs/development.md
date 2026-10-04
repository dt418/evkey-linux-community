# Development

`tools/dev.sh` is local Linux development harness. It never installs packages, runs as normal user, and never installs build output. Run from any directory; script resolves repository root from its own path, including paths containing spaces.

## Prerequisites

Target is Linux with CMake 3.16+, C++17 compiler, Fcitx5 development files 5.1.7+, Go 1.18+, gettext, and Python 3 with QtPy/PyQt, D-Bus, and GI bindings. Use system Python for distro packages; if `python3` points at non-system Python, set `PYTHON=/usr/bin/python3`.

On Debian/Ubuntu, install development dependencies represented by `packaging/debian/control` plus harness runtime dependencies:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  build-essential cmake golang extra-cmake-modules pkg-config gettext \
  fcitx5-modules-dev libfcitx5core-dev libfcitx5config-dev libfcitx5utils-dev \
  libinput-dev libudev-dev libsystemd-dev python3 python3-dbus python3-gi \
  python3-pyqt5 python3-qtpy dbus-daemon librsvg2-bin
```

For Debian package builds, use `mk-build-deps` or install every `Build-Depends` entry in `packaging/debian/control`; package-build tools such as `debhelper`, `dh-python`, and `dh-sequence-python3` are not needed by `tools/dev.sh`.

No harness command uses `sudo`, `apt`, package installation, or `cmake --install`.

## Agent skills

Agent instructions and terminology live in root `AGENTS.md` and `CONTEXT.md`. Project-local skills are versioned, not installed globally:

- Upstream [Superpowers](https://github.com/obra/superpowers) skills are pinned to commit `8ca22dba9a94f28898bbce59f2537ff4d87c747d` by `skills-lock.json`. MIT notice: `.agents/skills/SUPERPOWERS-LICENSE`.
- Project `evkey-engine`, `evkey-settings`, and `evkey-packaging` skills encode this repository's safety and acceptance boundaries.
- Codex discovers `.agents/skills/`. Claude Code's versioned copies live in `.claude/skills/`; their source stays under `.agents/skills/`.

```sh
npx --yes skills add https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d \
  --agent codex claude-code --skill '*' --copy --yes
```

This does not change global agent settings. Review `skills-lock.json` and skill diffs before adopting another upstream revision.

## AutoSkills

`autoskills@0.3.6 --dry-run` detected Bash and Python in this checkout, not the primary C++ or Go stack; its three suggestions were already marked installed. Project engine and packaging skills provide the missing domain coverage.

AutoSkills itself is CC BY-NC 4.0 and is not bundled here. Its detected skill sources and applicable licenses are documented in `.agents/skills/THIRD-PARTY-SOURCES.md`; skill files are separate from the project license. `python-executor` is flagged by the registry for arbitrary Python execution, network-capable libraries, and broad `Bash(belt *)` access; it requires the external `inference.sh` CLI. Keep project code and data local. Never send source, config, credentials, test data, or user text to that service unless user explicitly authorizes that specific transfer.

## Harness

```text
tools/dev.sh <help|check|dbus>
tools/dev.sh settings [unittest.dotted.selector ...]
```

| Command | Action |
| --- | --- |
| `tools/dev.sh help` | Print usage only. Does not inspect dependencies. `--help` and `-h` are aliases. |
| `tools/dev.sh check` | Configure CMake with `-DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=ON`; run `cmake --build "$BUILD_DIR" --parallel "$JOBS"` and `ctest --test-dir "$BUILD_DIR" --output-on-failure --parallel "$JOBS"`; run `go test ./...` in both `bamboo/` and `bamboo/bamboo-core/`; compile every `po/*.po` with `msgfmt --check` into temporary output. |
| `tools/dev.sh settings [selector ...]` | Run `test/settings-gui-startup.py` with `QT_QPA_PLATFORM=offscreen` and source `settings-gui` on `PYTHONPATH`. Each optional selector is dotted unittest name. |
| `tools/dev.sh dbus` | Run `test/settings-gui-dbus-owner-recovery.py` in `dbus-run-session`; test starts isolated Fcitx mock owner and requires Python D-Bus and GI bindings. |

Bad commands or unsupported arguments exit nonzero and print usage.


Optional environment overrides:

```sh
BUILD_DIR='/tmp/evkey build' JOBS=2 PYTHON=/usr/bin/python3 tools/dev.sh check
```

`BUILD_DIR` defaults to `<repository>/build/dev`. Relative `BUILD_DIR` resolves from repository root. `JOBS` must be positive integer; default detects CPUs and caps at four. `PYTHON` defaults to `python3` and applies to `settings` and `dbus`.

## Focused gates

Use narrow gate matching changed surface before full `check`:

```sh
tools/dev.sh settings
tools/dev.sh settings SettingsLanguageTest.test_system_default_uses_system_locale
tools/dev.sh dbus
ctest --test-dir build/dev -R 'preedit_lifecycle|fake_backspace_replacement' --output-on-failure
```

`ctest` command requires prior `tools/dev.sh check` configuration or equivalent CMake configuration. Run `tools/dev.sh check` before review or packaging; it includes complete CTest suite, both Go modules, and translation validation.
## Test-first seams

For behavior changes, use one red → green slice: write or select behavior test, run it until failure, make minimum change, then rerun same command. Refactoring belongs after green review, not inside slice.

- Settings UI seam: source Python test imports public Qt settings objects. Run `tools/dev.sh settings SettingsLanguageTest.test_system_default_uses_system_locale` for one dotted unittest seam.
- D-Bus recovery seam: `tools/dev.sh dbus` drives `LotusDBusHandler.get_config()` through isolated mock Fcitx owner restart; mock proves client recovery protocol, not desktop IME integration.
- Engine seam: CTest executable exposes composition behavior. Run `ctest --test-dir build/dev -R preedit_lifecycle --output-on-failure` after CMake configure.

Use known output/document behavior in assertions. Do not turn mock calls, private state, or source layout into test contract.


## Code map

- `src/lotus-engine.cpp`, `src/lotus-state.cpp`, and `src/lotus-config.h`: Fcitx addon, composition modes, configuration.
- `bamboo/` and `bamboo/bamboo-core/`: Vietnamese conversion engine and Go tests.
- `server/`: optional Smooth/uinput helper and protocol boundary.
- `settings-gui/`: QtPy settings client; `core/dbus_handler.py` owns Fcitx D-Bus connection.
- `test/`: CTest engine tests plus offscreen settings and isolated D-Bus recovery suites.
- `packaging/`: Debian, Fedora, and Arch packaging inputs.

## GUI: headless versus live

`tools/dev.sh settings` is offscreen test. It validates Python/Qt settings behavior but is not visible GUI proof and does not prove Fcitx integration.

For source-tree GUI launch in real graphical login session with Fcitx5 running:

```sh
PYTHONPATH="$PWD/settings-gui" python3 settings-gui/main.py
```

For installed GUI, first install only main runtime component from configured build tree, then select addon and launch settings:

```sh
sudo cmake --install build/dev --component Runtime
fcitx5-remote -s evkey
fcitx5-evkey-settings
```

`fcitx5-remote -s evkey` and live GUI launch require active user Fcitx5 D-Bus session. They are not valid in headless CI.

## Live smoke evidence

In native desktop session, add **EVKey Linux Community** to Fcitx5 and test installed addon rather than build-tree environment variables. In GTK, Qt, terminal, Firefox, and Chromium, enter Telex `Tooi ddang gox tieengs Vieetj.` and verify final document text is `Tôi đang gõ tiếng Việt.`; enter VNI `tie61ng Vie65t` and verify `tiếng Việt`.

For Preedit, verify underlined active composition before Space/Enter commits once. For Fake Backspace, verify immediate document replacement, Backspace only edits active composition, and focus changes do not modify another field. Use password field only to confirm raw input is preserved; never type real secrets.

Smooth requires separate optional helper installation and user-chosen service enablement:

```sh
sudo cmake --install build/dev --component Uinput
sudo systemctl enable --now "fcitx5-evkey-server@$(id -u).service"
```

Confirm GUI reports helper ready, then smoke Smooth in native GTK, Qt, browser, and terminal. Test lock/unlock, focus change, pointer movement, and helper loss without accepting unexpected text deletion. Disable afterward if no longer needed:

```sh
sudo systemctl disable --now "fcitx5-evkey-server@$(id -u).service"
```

Headless CTest, offscreen settings test, and mocked D-Bus recovery test are not native GUI, uinput, kernel-device, logind, X11, XWayland, or Wayland evidence. Native acceptance needs real desktop sessions with Fcitx5, systemd-logind, and `/dev/uinput`; record desktop/session type, Fcitx version, applications, and observed document text separately.
