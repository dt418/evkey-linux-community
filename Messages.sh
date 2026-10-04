#!/bin/bash

xgettext \
--language=C++ \
--from-code=UTF-8 \
--keyword=_ \
--keyword=N_ \
-o /tmp/evkey-cpp.pot \
$(find src server test -type f \( -name "*.cpp" -o -name "*.h" \))

xgettext \
--language=appdata \
--from-code=UTF-8 \
-o /tmp/evkey-xml.pot \
org.fcitx.Fcitx5.Addon.Evkey.metainfo.xml.in.in

xgettext \
--language=Python \
--from-code=UTF-8 \
--keyword=_ \
--keyword=N_ \
-o /tmp/evkey-python.pot \
$(find settings-gui -type f -name "*.py")

xgettext \
--language=Desktop \
--from-code=UTF-8 \
--keyword=Name \
--keyword=Comment \
-o /tmp/evkey-desktop.pot \
settings-gui/org.fcitx.Fcitx5.Addon.Evkey.Settings.desktop.in

{
    echo 'msgid ""'
    echo 'msgstr ""'
    echo '"Content-Type: text/plain; charset=UTF-8\n"'
    echo ""
    grep -hE "^Name=" \
    src/evkey.conf.in \
    src/evkey-addon.conf.in.in \
    | sort -u \
    | sed 's/^Name=\(.*\)/msgid "\1"\nmsgstr ""\n/'
} > /tmp/evkey-conf.pot

msgcat \
--use-first \
--sort-output \
/tmp/evkey-cpp.pot \
/tmp/evkey-xml.pot \
/tmp/evkey-conf.pot \
/tmp/evkey-python.pot \
/tmp/evkey-desktop.pot \
-o po/fcitx5-evkey.pot

rm -f /tmp/evkey-*.pot