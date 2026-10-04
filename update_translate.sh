#!/bin/sh
for po in po/*.po; do
    msgmerge --update "$po" po/fcitx5-evkey.pot;
done