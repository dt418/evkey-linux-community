#include "lotus-config.h"

#include <fcitx-config/rawconfig.h>

#include <iostream>
#include <string>

int main() {
    fcitx::lotusConfig config;
    fcitx::RawConfig description;
    config.dumpDescription(description);

    const auto& constDescription = description;
    const auto runtime = constDescription.get("lotusConfig/RuntimeStatus");
    if (!runtime) {
        std::cerr << "RuntimeStatus subconfig is not exposed by the addon config\n";
        return 1;
    }

    constexpr const char* runtimeUri = "fcitx://config/addon/evkey/runtime";
    bool foundUri = runtime->value() == runtimeUri;
    runtime->visitSubItems(
        [&foundUri, runtimeUri](const fcitx::RawConfig& item, const std::string&) {
            foundUri = foundUri || item.value() == runtimeUri;
            return true;
        },
        "", true);
    if (!foundUri) {
        std::cerr << "RuntimeStatus does not expose its Fcitx config URI\n";
        return 1;
    }
    return 0;
}
