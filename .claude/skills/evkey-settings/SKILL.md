---
name: evkey-settings
description: "Implement or review EVKey Linux Community native QtPy settings behavior: Fcitx D-Bus configuration, drafts and saves, owner reconnect, mode controls, dialogs, layout, accessibility, or localization. Use whenever changing `settings-gui/`, Settings tests, or user-visible configuration metadata."
---

# EVKey settings

Build native QtPy settings UI over Fcitx5 Controller D-Bus. It configures existing engine behavior; it does not implement a second input engine or global keyboard hook.

## Procedure

1. Read project-local upstream `systematic-debugging` before diagnosing an unknown failure and `test-driven-development` before adding behavior. Read `docs/development.md` for canonical UI/command map. Read `settings-gui/core/dbus_handler.py`, `settings-gui/ui/main_window.py`, and affected page before editing. For metadata-backed controls, also read `src/lotus-config.h`; for translations read `settings-gui/i18n.py`, `po/`, and relevant templates. **Done:** each requested control maps to one existing config key, subconfig URI, or Fcitx action.

2. Keep one owner for each value. `LotusSettingsWindow` owns top controls (`InputMethod`, `OutputCharset`, `Mode`); `DynamicSettingsPage` owns its `modified_values`; editor dialogs own their own subconfig drafts. Reuse `MacroEditorPage`, `ModeManagerPage`, `HotkeyEditorWidget`, and existing dynamic metadata paths. Preserve available backend menus/options in advanced UI rather than fabricating EVKey-branded switches. **Done:** no duplicate widget writes same setting and all shown controls change real backend state.

3. Make D-Bus state explicit. Use `LotusDBusHandler` and `fcitx://config/addon/evkey`; runtime status comes read-only from `fcitx://config/addon/evkey/runtime` through `get_runtime_status()`. Keep runtime status separate from persisted settings. On unavailable D-Bus, preserve user draft, disable save, show recoverable error, and reconnect through existing owner-aware flow. **Done:** disconnected UI never presents defaults as live config and reconnect does not discard edits.

4. Save safely. Merge a page's `modified_values` with freshly read values as `DynamicSettingsPage.save_data` does. Retry only reads after confirmed D-Bus owner loss through `_call_controller(..., retry_owner_loss=True)`; do not retry `SetConfig` blindly because completion may be unknown. Keep failed changes in draft and report which scope failed. `restore_defaults` stages metadata defaults without reloading away staged choices; it does not erase macro/app-rule data unless that editor explicitly owns it. **Done:** each write has one deliberate attempt, draft survives failure, and successful scope state is truthful.

5. Keep mode UX aligned with engine. Primary controls are Preedit, Fake Backspace, and Uinput (Smooth); other `LotusMode` values stay reachable through advanced mode UI. Preserve stable IDs in `mode_manager.py`, `ModeOrder`, `ShowMode*`, and shortcut mappings. Reject duplicate shortcuts before save. Explain helper fallback through actual `RequestedMode`, `EffectiveMode`, `Reason`, and `HelperReady`, never a decorative success banner. **Done:** selected mode, persisted value, and runtime fallback status agree.

6. Maintain native Qt behavior. Keep light/dark palette, logical size/scrolling, minimum control height, tab order, focus visibility, accessible names, translated strings, and high-DPI layout intact. The typing field remains `QPlainTextEdit` using system IME; Python must not transform its text. **Done:** UI change has no hardcoded desktop/workstation path and localized visible text follows existing gettext flow.

7. For one new observable UI/configuration behavior or regression, follow upstream `test-driven-development`: make focused coverage red at existing seam, make production behavior green, then run real smoke from `docs/development.md`. Do not claim existing Settings code was developed TDD. `test/settings-gui-startup.py` covers UI/draft/recovery shape; `test/settings-gui-dbus-owner-recovery.py` covers mocked owner recovery. State scope precisely: offscreen Qt and mocked D-Bus are not native desktop or real Fcitx proof. **Done:** changed save/reconnect/layout contract has red-to-green focused coverage and corresponding real smoke evidence, or no executable seam exists and limitation is explicit.

## Guardrails

- Do not write global desktop shortcuts, edit `/etc/environment`, change IME selection, run GUI as root, or kill Fcitx from Settings.
- “Turn off input method” uses existing Fcitx switching behavior; closing Settings never stops engine.
- Do not read process lists as universal Wayland focus evidence. Per-app rules use existing engine program naming and state their limitation.
- Do not add UI-only options without backend configuration or action.

## Stop

Stop when requested Settings behavior reaches D-Bus, draft/save/recovery state, native UI, and localization without lying about runtime status. Use `docs/development.md` for command and native-validation details; keep this skill procedural.
