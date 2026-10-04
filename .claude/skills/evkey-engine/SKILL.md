---
name: evkey-engine
description: "Implement or review EVKey Fcitx5 input-engine behavior: input modes, text replacement, focus/capability lifecycle, per-context state, or optional uinput helper protocol. Use whenever changing `src/lotus-*.{cpp,h}`, `server/lotus-server.*`, `src/lotus-protocol.h`, or engine behavior tests."
---

# EVKey engine

Work on native Fcitx5 C++17 engine and Bamboo bridge. Public product IDs are `evkey` and `fcitx5-evkey`; private `LotusEngine`, `LotusState`, and `lotus-*` filenames remain source-continuity names.

## Procedure

1. Read project-local upstream `systematic-debugging` before diagnosing an unknown failure and `test-driven-development` before adding behavior. Read `docs/development.md` for implementation map and commands. Then read only behavior owners: `src/lotus-config.h`, `src/lotus-engine.{h,cpp}`, `src/lotus-state.{h,cpp}`, and `src/lotus-protocol.h`; read `server/lotus-server.{h,cpp}` and `misc/` when helper behavior changes. **Done:** requested behavior maps to one mode/config path, one `LotusState` lifecycle path, and, if applicable, one helper boundary.

2. Preserve configuration contract. Keep `LotusMode` numeric mapping in `modeToInt`/`intToMode` stable; appended `FakeBackspace` is ID 9. Reuse Bamboo options and existing mode/menu/app-rule machinery instead of inventing typing features. Keep global/rule choice separate from `requestedMode_`, `effectiveMode_`, and `modeReason_`. **Done:** config, mode selection, and status describe same real behavior without changing unrelated options.

3. Change composition through `LotusState` only. Reuse `EngineProcessKeyEvent`, `EnginePullCommit`, `EnginePullPreedit`, `ResetEngine`, `compareAndSplitStrings`, `checkForwardSpecialKey`, and existing replacement paths. Preserve Preedit client/panel behavior and one-time commit on boundaries. For Fake Backspace, forward Backspace key press/release to client then commit added text; do not connect helper or use `deleteSurroundingText`. **Done:** text ownership, accepted/forwarded event ordering, and buffer reset are explicit for every changed branch.

4. Apply lifecycle guards before processing text. `PasswordOrSensitive` and `Disable` reset state and forward original input. Focus, mode, capability, cursor/selection, external surrounding-text mismatch, helper disconnect, and reset invalidate stale replacement state; increment `compositionGeneration_` where state becomes stale. Pending helper completion belongs to originating `InputContext` and generation, never a newly focused context. Do not log keystrokes, preedit, commits, macro values, diffs, or other typed content. **Done:** stale/asynchronous path cannot delete or commit into another context, and sensitive paths retain no transformation state.

5. Treat Smooth/Uinput as optional privileged transport. Validate wire-v1 requests with `kb_request_is_valid`; `KbRequest` is 20-byte little-endian and `KbResponse` 8-byte little-endian. Keep `KbOp`, `KbStatus`, count, and delay limits synchronized among `src/lotus-protocol.h`, engine, server, and `test/kb-socket-listener.h`. Probe before direct replacement; helper/session/protocol failure falls back to effective Preedit before a new composition, while interrupted in-flight replacement stops safely rather than replaying into unknown text. **Done:** no raw-key “success” fallback, no blind retry, no unbounded buffered keys, and protocol endpoints agree.

6. For one new observable behavior or regression, follow upstream `test-driven-development`: add or adjust one focused seam so it goes red, make production change until green, then run real smoke from `docs/development.md`. Do not claim pre-existing code was developed TDD. Use `TestInputContext` for deterministic engine contracts: `preedit_lifecycle`, `fake_backspace_replacement`, `smooth_buffered_key_replay`, `select_mode_replacement`, and `app_rule_reset` are useful patterns. Label socket/mock coverage headless; it does not prove native GUI, Wayland/X11, kernel uinput, or logind behavior. **Done:** one changed observable contract has red-to-green focused coverage and corresponding real smoke evidence, or change has no executable seam and limitation is explicit.

## Guardrails

- Native proof requires installed package in real desktop session; source-tree tests, socket listeners, and mocks are evidence only for their stated boundary.
- Keep replacement bounded by `MAX_BUFFERED_KEYS`; cancel interrupted helper work and preserve existing document rather than guessing application state.
- Keep helper security boundary: peer UID checks, active local unlocked `seat0` session gate, keyboard exclusion from pointer monitoring, dedicated `evkey-input` account, empty capabilities, and no automatic service enablement.
- Do not weaken udev ACLs, systemd sandboxing, session checks, or protocol validation to make a test pass.

## Stop

Stop when requested engine behavior is implemented across its config, lifecycle, transport, and focused red-to-green behavior test; no typed-content logging or cross-context path remains. Use `docs/development.md` for build, test, and native-validation commands; do not duplicate command tables here.
