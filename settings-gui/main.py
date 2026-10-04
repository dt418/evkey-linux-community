#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Nguyen Hoang Ky <nhktmdzhg@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Application entry point.
"""

import signal
import sys

from i18n import setup_i18n
from qtpy.QtCore import QSettings
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication
from ui.main_window import LotusSettingsWindow


def main():
    """Main execution function."""
    app = QApplication(sys.argv)
    app.setOrganizationName("EVKey Linux Community")
    app.setDesktopFileName("org.fcitx.Fcitx5.Addon.Evkey.Settings")
    app.setApplicationName("fcitx5-evkey-settings")
    setup_i18n(QSettings().value("ui/language", "system"))
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.setWindowIcon(QIcon.fromTheme("fcitx-evkey"))


    window = LotusSettingsWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        app.quit()


if __name__ == "__main__":
    main()
