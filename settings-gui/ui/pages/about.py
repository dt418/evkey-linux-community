# SPDX-FileCopyrightText: 2026 Nguyen Hoang Ky <nhktmdzhg@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from i18n import _
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from version import __version__
except ImportError:
    __version__ = "dev version"  # Fallback for local development


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Root layout for this widget
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area to handle overcrowding
        scroll = QScrollArea()
        scroll.setObjectName("AboutScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_widget.setObjectName("AboutContent")

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(10)

        # Logo/Icon
        try:
            pixmap = QIcon.fromTheme("fcitx-evkey").pixmap(56, 56)
            if pixmap.isNull():
                logo = QLabel("V")
                logo.setStyleSheet("font-size: 64px; font-weight: 700; margin-bottom: 5px;")
            else:
                logo = QLabel()
                logo.setPixmap(pixmap)
                logo.setStyleSheet("margin-bottom: 5px;")
        except Exception:
            logo = QLabel("V")
            logo.setStyleSheet("font-size: 64px; font-weight: 700; margin-bottom: 5px;")

        layout.addWidget(logo, alignment=Qt.AlignCenter)

        title = QLabel(_("EVKey Linux Community"))
        title.setObjectName("AboutTitle")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        version = QLabel(_("Version {}").format(__version__))
        version.setObjectName("VersionTag")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("""
            QLabel#VersionTag {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(version, alignment=Qt.AlignCenter)

        desc = QLabel(
            _("Bản cộng đồng lấy cảm hứng từ EVKey; sử dụng Lotus/Bamboo, không phải bản EVKey chính thức.")
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setObjectName("AboutDescription")
        layout.addWidget(desc, alignment=Qt.AlignCenter)

        upstream_info = QLabel(
            _("Independent community project. See installed license files for source and upstream acknowledgements.")
        )
        upstream_info.setWordWrap(True)
        upstream_info.setAlignment(Qt.AlignCenter)
        upstream_info.setObjectName("AboutSourceInfo")
        layout.addWidget(upstream_info)

        # Keep legal text close to project identity; scroll only when viewport requires it.

        # Footer (Open Source Licenses)
        footer_line = QFrame()
        footer_line.setFrameShape(QFrame.HLine)
        footer_line.setObjectName("AboutLine")
        layout.addWidget(footer_line)

        license_title = QLabel(_("Open Source Licenses"))
        license_title.setObjectName("CreditsTitle")
        layout.addWidget(license_title)

        # Main License
        main_license_info = QLabel(
            _(
                "This project is licensed under the <b>GNU General Public License v3.0 or later (GPL-3.0-or-later)</b>."
            )
        )
        main_license_info.setWordWrap(True)
        main_license_info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        main_license_info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        main_license_info.setObjectName("MainLicenseInfo")
        layout.addWidget(main_license_info)

        # Third-party & Upstream Info
        third_party_info = QLabel(
            _(
                "Based on Lotus, licensed under <b>GPL-3.0-or-later</b>, and Bamboo, licensed under the <b>MIT License</b>.<br>"
                "Upstream authors retain their copyright."
            )
        )
        third_party_info.setWordWrap(True)
        third_party_info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        third_party_info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        third_party_info.setObjectName("ThirdPartyLicenseInfo")
        layout.addWidget(third_party_info)

        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll)
