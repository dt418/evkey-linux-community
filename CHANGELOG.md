# Changelog

## 1.0.0 — EVKey Linux Community

- Show available Wayland/X11 display backends when XDG session metadata is absent, without guessing active session type.
- Present activation guide in a palette-aware native dialog with actual line breaks.
- Keep complete backend-provided input-method and charset menus visible in compact controls; preserve Bamboo's combined modes and X-Unikey-compatible VIQR `*` behavior without inventing unsupported aliases.
- Rebuild settings front page as compact EVKey-style controls with common options, saved expansion state, explicit dirty status, and responsive grouped system actions.
- Drive Vietnamese activation through Fcitx Controller state; show configured global toggle keys read-only and open Fcitx config tool to change them.
- Expose recent EVKey-context helper fallback as read-only runtime status; explain context scope and auto-open advanced mode when Uinput falls back.
- Register read-only runtime-status subconfig so Fcitx D-Bus resolves the settings query.
- Localize new controls and keep existing dictionary, macro, keymap, backup, shortcut, and About/license editors reachable.
- Add status-menu selectors for typing method and output charset; keep selection synchronized with saved Fcitx configuration.
- Recover settings reads when Fcitx5's D-Bus owner changes, probe owner during backoff, bound synchronous calls, and preserve drafts with accurate reconnect status.
- Retry safe Controller operations after Fcitx owner changes; invalidate stale connections without replaying ambiguous writes.
- Reload unmodified Settings tabs after automatic reconnection, including startup without Fcitx; preserve unsaved page changes.
- Hide stale tab configuration errors immediately when live Fcitx recovery succeeds.
- Restore scrollbars when Basic and Shortcuts tabs reload dynamic settings.
- Fix settings-window startup crash when populating controls or retrying configuration.
- Add Nix flake package outputs and an opt-in NixOS module for the helper account, udev access, and systemd unit.
- Compact About page layout for classic settings density and keep license text reachable at constrained window sizes.
- Keep System actions reachable by scrolling when expanded controls reduce available height.
- Default Settings language to the system locale; allow persistent English or Vietnamese app-only override.
- Complete Vietnamese Settings headings and runtime/fallback messages; remove stale fuzzy translations.

- Verify Fcitx applies requested EVKey activation state; show failures in palette-aware native dialogs and actionable runtime-status guidance.

- Rebrand imported Fcitx5 Lotus/Bamboo input engine as independent EVKey Linux Community edition; isolate config, icons, desktop entry, translations, and package names.
- Add Fake Backspace mode and per-input-context effective-mode fallback when Smooth helper unavailable.
- Add optional uinput helper with peer/session checks, constrained pointer monitoring, framed local protocol, and split runtime/helper packaging.
- Replace settings front page with native controls, connection recovery, Vietnamese disclaimer, and advanced editors.
- No release-signing or automatic publishing workflow.
