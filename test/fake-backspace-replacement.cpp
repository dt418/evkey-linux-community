// SPDX-License-Identifier: GPL-3.0-or-later
#include "lotus-engine.h"
#include "test-input-context.h"

#include <fcitx-utils/keysym.h>

#include <iostream>
#include <memory>
#include <string>
#include <vector>

int main() {
    configureTestPaths("fcitx5-evkey-fake-backspace-replacement");
    TestInstance       testInstance;
    fcitx::LotusEngine engine(&testInstance.instance);
    fcitx::RawConfig   config;
    config.setValueByPath("Mode", "Fake Backspace");
    config.setValueByPath("InputMethod", "Telex");
    engine.setConfig(config);

    if (engine.config().mode.value() != fcitx::LotusMode::FakeBackspace || engine.config().inputMethod.value() != "Telex") {
        std::cerr << "Fake Backspace/Telex config failed\n";
        return 1;
    }

    auto context = std::make_unique<TestInputContext>(&testInstance.instance);
    context->focusIn();
    fcitx::InputMethodEntry entry("evkey", "EVKey Linux Community", "vi", "evkey");
    fcitx::InputContextEvent focus(context.get(), fcitx::EventType::InputContextFocusIn);
    engine.activate(entry, focus);

    for (const auto symbol : {FcitxKey_a, FcitxKey_s}) {
        fcitx::KeyEvent event(context.get(), fcitx::Key(symbol), false);
        engine.keyEvent(entry, event);
        if (!event.accepted()) {
            std::cerr << "Fake Backspace rejected Telex key " << symbol << '\n';
            return 1;
        }
    }

    const std::vector<std::string> expectedCommits{"a", "á"};
    if (context->commits() != expectedCommits) {
        std::cerr << "Expected commits ['a']['á'], got " << context->commits().size() << " commit(s)\n";
        return 1;
    }

    const auto& forwarded = context->forwarded();
    if (forwarded.size() != 2 || forwarded[0].key().sym() != FcitxKey_BackSpace || forwarded[0].isRelease() ||
        forwarded[1].key().sym() != FcitxKey_BackSpace || !forwarded[1].isRelease()) {
        std::cerr << "Expected one Backspace press/release pair for replaced Telex character\n";
        return 1;
    }
    return 0;
}
