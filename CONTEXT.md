# EVKey Linux Community

Vietnamese text composition for Linux applications through Fcitx5. This community edition is inspired by EVKey and uses Lotus/Bamboo; it is not an official EVKey release.

## Language

**Input method**: The rules that turn keystrokes into Vietnamese characters, such as Telex or VNI.
_Avoid_: mode, transport.

**Output charset**: The representation of composed Vietnamese text, such as Unicode or a legacy Vietnamese encoding.
_Avoid_: input method.

**Input mode**: The mechanism used to present or replace composed text in the application.
_Avoid_: input method, typing style.

**Preedit**: Composition shown separately from committed application text until the word is accepted.
_Avoid_: prediction, autocomplete.

**Fake Backspace**: Direct composition that replaces the previously emitted suffix using application-directed Backspace events and committed text; it does not use the privileged helper.
_Avoid_: Smooth, surrounding-text deletion.

**Smooth / Uinput**: Direct composition using an optional helper's virtual keyboard for editing keys; composed text still travels through Fcitx.
_Avoid_: universal application compatibility, hardware Unicode typing.

**Requested mode**: The user's saved global or application-specific mode choice.
_Avoid_: effective mode.

**Effective mode**: The mode currently permitted for a particular input context, possibly differing from the requested mode because of compatibility or helper availability.
_Avoid_: saved mode.

**Input context**: One application's text-entry interaction, with its own focus, capabilities and composition ownership.
_Avoid_: desktop session, settings window.

**Composition**: The current word being transformed by the engine, distinct from previously committed document text.

**Replacement**: An edit that removes the engine-owned old suffix and emits its transformed suffix. Acceptance by the helper is not proof that the application applied the edit.

**Surrounding text**: Application-provided text and cursor/selection positions used to determine whether an earlier emitted suffix is still safe to edit.

**Application rule**: A mode preference for an identifiable application, overriding the global choice; unidentified applications use the global choice.

**Helper**: The optional privileged process permitted to emit limited editing keys in an eligible local desktop session. Installing it and enabling it are separate user decisions.

**Draft**: A Settings change not yet saved to Fcitx; reconnection does not authorize discarding or applying it.

**Runtime status**: Read-only information about recent input-context behavior and fallback, not a guarantee of compatibility with every application.
