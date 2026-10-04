// SPDX-License-Identifier: GPL-3.0-or-later
#include "kb-socket-listener.h"
#include "lotus-engine.h"
#include "test-input-context.h"

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace {

    bool receiveBackspaceRequest(KbSocketListener& listener, fcitx::LotusEngine& engine, TestInputContext& context, size_t& count, const char* meaning,
                                 const char* timeoutExpected = "request within 5000 ms") {
        KbRequest request{};
        if (!listener.receive(request, meaning, timeoutExpected))
            return false;
        if (request.op != KbOp::Backspace) {
            reportFailure("receive replacement request", "op=Backspace",
                          "op=" + std::to_string(static_cast<std::uint32_t>(request.op)) + ", count=" + std::to_string(request.count), meaning);
            return false;
        }
        count = request.count;
        return fcitx::LotusTestAccess::completeResponse(engine, context, meaning);
    }

    bool send(fcitx::LotusEngine& engine, const fcitx::InputMethodEntry& entry, TestInputContext& context, fcitx::KeySym symbol, bool requireAccepted) {
        fcitx::KeyEvent event(&context, fcitx::Key(symbol), false);
        engine.keyEvent(entry, event);
        if (event.accepted() != requireAccepted) {
            reportFailure("process key " + std::to_string(symbol), "accepted=" + std::to_string(static_cast<int>(requireAccepted)),
                          "accepted=" + std::to_string(static_cast<int>(event.accepted())) + ", commits=" + std::to_string(context.commits().size()),
                          "Smooth buffered-key handling accepted or rejected the key unexpectedly");
            return false;
        }
        return true;
    }

} // namespace

int main() {
    configureTestPaths("fcitx5-evkey-smooth-buffered-key-replay");
    TestInstance       testInstance;
    fcitx::LotusEngine engine(&testInstance.instance);
    fcitx::RawConfig   config;
    config.setValueByPath("Mode", "Uinput (Smooth)");
    config.setValueByPath("InputMethod", "Telex");
    engine.setConfig(config);
    if (engine.config().mode.value() != fcitx::LotusMode::Smooth || engine.config().inputMethod.value() != "Telex") {
        reportFailure("configure Smooth/Telex", "mode=Smooth, input method=Telex", "configured mode or input method differs",
                      "the replay test cannot exercise Smooth Telex behavior");
        return 1;
    }

    KbSocketListener listener;
    if (!listener.valid())
        return 1;
    auto context = std::make_unique<TestInputContext>(&testInstance.instance);
    context->focusIn();
    fcitx::InputMethodEntry  entry("evkey", "EVKey Linux Community", "vi", "evkey");
    fcitx::InputContextEvent focus(context.get(), fcitx::EventType::InputContextFocusIn);
    engine.activate(entry, focus);

    if (!fcitx::LotusTestAccess::completeProbe(listener, engine, *context, "Smooth mode helper probe did not complete"))
        return 1;
    context->resetPreeditUpdateCount();

    // Telex a, s changes real Bamboo preedit a -> á. Smooth mode replaces
    // old character through helper keyboard transport.
    if (!send(engine, entry, *context, FcitxKey_a, false) || !send(engine, entry, *context, FcitxKey_s, true))
        return 1;
    size_t backspaces = 0;
    if (!receiveBackspaceRequest(listener, engine, *context, backspaces, "the initial Telex replacement request did not arrive"))
        return 1;

    if (!send(engine, entry, *context, FcitxKey_x, true) || !context->commits().empty()) {
        reportFailure("buffer key x before deletion completes", "no immediate commits", "commits=" + std::to_string(context->commits().size()),
                      "buffered key x was emitted before the first replacement completed");
        return 1;
    }
    for (size_t i = 0; i < backspaces; ++i) {
        if (!send(engine, entry, *context, FcitxKey_BackSpace, i + 1 == backspaces))
            return 1;
    }

    size_t replayBackspaces = 0;
    if (!receiveBackspaceRequest(listener, engine, *context, replayBackspaces, "buffered key was not replayed after deletion",
                                 "buffered x replay starts another replacement request within 5000 ms"))
        return 1;
    for (size_t i = 0; i < replayBackspaces; ++i) {
        if (!send(engine, entry, *context, FcitxKey_BackSpace, i + 1 == replayBackspaces))
            return 1;
    }

    const std::vector<std::string> expected{"á", "ã"};
    if (context->commits() != expected) {
        std::string actual = "commits=";
        for (const auto& commit : context->commits())
            actual += "['" + commit + "']";
        const auto meaning = "the buffered key replay did not produce the expected final commits; "
                             "first-backspaces=" +
            std::to_string(backspaces) + ", replay-backspaces=" + std::to_string(replayBackspaces);
        reportFailure("verify final replay commits", "commits=['á']['ã']", actual, meaning);
        return 1;
    }
    return 0;
}
