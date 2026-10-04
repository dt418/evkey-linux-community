// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * @file app-rule-reset.cpp
 * @brief Headless regression test: each input context keeps its resolved
 *        application mode after a configuration reload.
 *
 * The mock app "test" has an Off rule while global mode is Preedit. The test
 * inspects the per-context mode label before and after reload; global state
 * must not mask or overwrite that context's effective mode.
 */

#include "lotus-engine.h"
#include "test-input-context.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>

namespace {

    void reportFailure(const std::string& step, const std::string& expected, const std::string& actual, const std::string& meaning) {
        std::cerr << "Step: " << step << '\n';
        std::cerr << "Expected: " << expected << '\n';
        std::cerr << "Actual: " << actual << '\n';
        std::cerr << "Meaning: " << meaning << '\n';
    }


} // namespace

int main() {
    const char* testName = "fcitx5-evkey-app-rule-reset";
    configureTestPaths(testName);
    const auto rulesFile = std::filesystem::temp_directory_path() / testName / "config/fcitx5/conf/evkey-app-rules.conf";
    {
        std::ofstream file(rulesFile, std::ios::trunc);
        if (!file.is_open()) {
            reportFailure("write app rules file", "file open", rulesFile.string(), "the test needs the app rule on disk");
            return 1;
        }
        file << "test=0\n";
    }

    TestInstance       testInstance;
    fcitx::LotusEngine engine(&testInstance.instance);

    // Global mode Preedit, differing from the app's Off rule.
    fcitx::RawConfig config;
    config.setValueByPath("Mode", "Preedit");
    config.setValueByPath("InputMethod", "Telex");
    engine.setConfig(config);
    if (engine.config().mode.value() != fcitx::LotusMode::Preedit) {
        reportFailure("configure global Preedit", "mode=Preedit", "global mode differs", "the test needs the global mode to differ from the app rule");
        return 1;
    }

    auto context = std::make_unique<TestInputContext>(&testInstance.instance);
    context->focusIn();
    fcitx::InputMethodEntry  entry("evkey", "EVKey Linux Community", "vi", "evkey");
    fcitx::InputContextEvent focus(context.get(), fcitx::EventType::InputContextFocusIn);
    engine.activate(entry, focus);

    const auto actualMode = engine.subModeLabelImpl(entry, *context);
    if (actualMode != "EVKey Linux Community - Off") {
        reportFailure("activate with rule Off", "EVKey Linux Community - Off", actualMode, "activate() must resolve the per-app rule for this input context");
        return 1;
    }

    // Simulate a config reload / a new input context appearing without any
    // focus change: setEngine() runs for every context but must not clobber the
    // focused window's resolved rule.
    fcitx::RawConfig reloaded;
    reloaded.setValueByPath("Mode", "Preedit");
    reloaded.setValueByPath("InputMethod", "Telex");
    engine.setConfig(reloaded);

    const auto reloadedMode = engine.subModeLabelImpl(entry, *context);
    if (reloadedMode != "EVKey Linux Community - Off") {
        reportFailure("config reload keeps focused app rule", "EVKey Linux Community - Off", reloadedMode,
                      "config reload must preserve this context's resolved application rule");
        return 1;
    }

    return 0;
}
