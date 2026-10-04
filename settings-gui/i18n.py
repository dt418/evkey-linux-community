# SPDX-FileCopyrightText: 2026 Nguyen Hoang Ky <nhktmdzhg@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Internationalization setup for the application.
"""

import gettext
import locale


_translation = gettext.NullTranslations()


def setup_i18n(language="system"):
    """Initialize gettext using the system locale or an app-only override."""
    global _translation
    try:
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        print(f"Failed to initialize system locale: {e}")

    domain = "fcitx5-evkey"
    localedir = "/usr/share/locale"
    if language == "en":
        _translation = gettext.NullTranslations()
    else:
        languages = ["vi"] if language == "vi" else None
        try:
            _translation = gettext.translation(
                domain,
                localedir,
                languages=languages,
                fallback=True,
            )
        except Exception as e:
            print(f"Failed to initialize i18n: {e}")
            _translation = gettext.NullTranslations()


def _(text):
    return _translation.gettext(text)


def N_(text):
    """Marker for strings that should be translated lazily."""
    return text
