# SPDX-FileCopyrightText: 2026 Nguyen Hoang Ky <nhktmdzhg@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compact native configuration window for EVKey Linux Community."""

import os

from core.dbus_handler import LotusDBusHandler
from i18n import _
from qtpy.QtCore import QProcess, QSettings, Qt, QTimer
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class EditorDialog(QDialog):
    """Host existing editors without duplicating their settings in main window."""

    def __init__(self, title, page, parent=None):
        super().__init__(parent)
        self.page = page
        self.setWindowTitle(title)
        save_button = QDialogButtonBox.Save if hasattr(page, "save_data") else QDialogButtonBox.NoButton
        close_button = QDialogButtonBox.Close
        self.resize(720, 540)
        if save_button == QDialogButtonBox.NoButton:
            self.resize(600, 500)
            self.setMinimumSize(480, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(page)

        self.buttons = QDialogButtonBox(save_button | close_button)
        if save_button != QDialogButtonBox.NoButton:
            self.buttons.button(QDialogButtonBox.Save).clicked.connect(self._save)
        self.buttons.rejected.connect(self._close)
        layout.addWidget(self.buttons)

    def _save(self):
        if hasattr(self.page, "has_validation_errors") and self.page.has_validation_errors():
            message = self.page.validation_message()
            QMessageBox.warning(self, _("Cannot Save"), message)
            return
        if hasattr(self.page, "save_data") and self.page.save_data() is False:
            QMessageBox.critical(self, _("Error"), _("Failed to save settings. Please check if Fcitx5 is running."))
            return
        self.accept()

    def _close(self):
        if hasattr(self.page, "is_modified") and self.page.is_modified():
            confirmation = QDialog(self)
            confirmation.setObjectName("DiscardConfirmation")
            confirmation.setWindowTitle(_("Discard Changes"))
            layout = QVBoxLayout(confirmation)
            message = QLabel(_("Discard unsaved changes?"))
            message.setObjectName("DiscardPrompt")
            message.setPalette(self.palette())
            message.setAutoFillBackground(True)
            message.setWordWrap(True)
            layout.addWidget(message)
            buttons = QDialogButtonBox(
                QDialogButtonBox.Discard | QDialogButtonBox.Cancel
            )
            buttons.button(QDialogButtonBox.Cancel).setDefault(True)
            buttons.button(QDialogButtonBox.Discard).clicked.connect(
                confirmation.accept
            )
            buttons.rejected.connect(confirmation.reject)
            layout.addWidget(buttons)
            if confirmation.exec() != QDialog.Accepted:
                return
        self.reject()


class PageGroup(QWidget):
    """Small dialog page group with one explicit save operation."""

    def __init__(self, pages, parent=None):
        super().__init__(parent)
        self.pages = pages
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        for title, page in pages:
            tabs.addTab(page, title)
        layout.addWidget(tabs)

    def is_modified(self):
        return any(hasattr(page, "is_modified") and page.is_modified() for _, page in self.pages)

    def has_validation_errors(self):
        return any(
            hasattr(page, "has_validation_errors") and page.has_validation_errors()
            for _, page in self.pages
        )

    def validation_message(self):
        return "\n".join(
            page.validation_message()
            for _, page in self.pages
            if hasattr(page, "validation_message") and page.validation_message()
        )

    def save_data(self):
        for _, page in self.pages:
            if hasattr(page, "save_data") and page.save_data() is False:
                return False
        return True


class LotusSettingsWindow(QMainWindow):
    """Native settings application. Private Lotus class name remains for source continuity."""

    PRIMARY_MODES = {
        "Preedit": _("Preedit — show underlined composition before committing."),
        "Fake Backspace": _("Fake Backspace — replace text through application backspace events."),
        "Uinput (Smooth)": _("Uinput (Smooth) — optional helper performs smooth key replacement."),
    }
    CONTROL_KEYS = ("InputMethod", "OutputCharset", "Mode")
    INPUT_METHOD_LABELS = {
        "Microsoft layout": _("Microsoft"),
        "Custom": _("Custom"),
    }
    OUTPUT_CHARSET_ORDER = (
        "Unicode",
        "TCVN3 (ABC)",
        "VNI Windows",
        "VIQR",
        "Windows 1258 codepage",
        "Unicode tổ hợp",
        "UTF-8",
        "NCR Decimal",
        "NCR Hex",
        "Unicode C string Hex",
        "Unicode C string Decimal",
        "VISCII",
        "VPS",
        "BKHCM 2",
        "BKHCM 1",
        "Vietware X",
        "Vietware Full",
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle(_("EVKey Linux Community Settings"))
        self.setWindowIcon(QIcon.fromTheme("fcitx-evkey"))
        self.dbus_handler = LotusDBusHandler()
        self.control_values = {}
        self.control_initial_values = {}
        self.control_metadata = {}
        self.control_widgets = {}
        self.control_dirty = {}
        self.ui_settings = QSettings()
        self._fallback_expanded_for = None
        self.controls_available = False


        self._setup_ui()
        self._setup_window_size()
        self._apply_global_styles()
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(self._poll_connection_status)
        self.status_timer.start()
        self._load_controls()
        self._refresh_fcitx_status()
        self._refresh_runtime_status()

    def _apply_global_styles(self):
        self.setStyleSheet(
            """
            QLabel#ConnectionStatus[connected="false"] { color: palette(text); }
            QLabel#DraftStatus { color: palette(mid); }
            QLabel#RuntimeStatus { padding: 4px 0; }
            QPushButton { min-height: 30px; }
            QPushButton#Primary { font-weight: 600; }
            QPushButton#VietnameseToggle[active="true"] {
                background: palette(highlight);
                color: palette(highlighted-text);
                font-weight: 600;
            }
            QGroupBox { font-weight: 600; }
            """
        )

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(8)

        top_row = QHBoxLayout()
        self.vietnamese_toggle = QPushButton()
        self.vietnamese_toggle.setObjectName("VietnameseToggle")
        self.vietnamese_toggle.clicked.connect(self._toggle_vietnamese)
        top_row.addWidget(self.vietnamese_toggle)
        self.current_input_status = QLabel(_("Fcitx input state: checking…"))
        self.current_input_status.setWordWrap(True)
        top_row.addWidget(self.current_input_status, 1)
        self.toggle_hotkey_status = QLabel(_("Toggle shortcut: checking…"))
        top_row.addWidget(self.toggle_hotkey_status)
        self.change_hotkey_button = QPushButton(_("Change…"))
        self.change_hotkey_button.clicked.connect(self._open_fcitx_config)
        top_row.addWidget(self.change_hotkey_button)
        root.addLayout(top_row)

        status_row = QHBoxLayout()
        self.connection_status = QLabel()
        self.connection_status.setObjectName("ConnectionStatus")
        self.connection_status.setWordWrap(True)
        self.retry_button = QPushButton(QIcon.fromTheme("view-refresh"), _("Retry"))
        self.retry_button.clicked.connect(self._retry_connection)
        status_row.addWidget(self.connection_status, 1)
        status_row.addWidget(self.retry_button)
        root.addLayout(status_row)

        self.controls_group = QGroupBox(_("Controls"))
        controls_layout = QVBoxLayout(self.controls_group)
        controls_layout.setSpacing(6)
        self.controls_form = QFormLayout()
        self.controls_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        controls_layout.addLayout(self.controls_form)

        mode_layout = QHBoxLayout()
        self.mode_buttons = QButtonGroup(self)
        for mode, description in self.PRIMARY_MODES.items():
            radio = QRadioButton(_(mode))
            radio.setProperty("mode", mode)
            radio.setToolTip(description)
            radio.toggled.connect(lambda checked, value=mode: checked and self._set_mode(value))
            self.mode_buttons.addButton(radio)
            mode_layout.addWidget(radio)
        mode_layout.addStretch()
        controls_layout.addLayout(mode_layout)

        self.runtime_status = QLabel(_("Helper status follows the most recent Fcitx input context."))
        self.runtime_status.setWordWrap(True)
        self.runtime_status.setObjectName("RuntimeStatus")
        self.runtime_status.hide()
        controls_layout.addWidget(self.runtime_status)

        self.more_button = QPushButton(_("More modes"))
        self.more_button.setCheckable(True)
        self.more_button.setChecked(self.ui_settings.value("ui/expanded", False, type=bool))
        self.more_button.setText(
            _("Fewer modes") if self.more_button.isChecked() else _("More modes")
        )
        self.more_button.toggled.connect(self._set_more_expanded)
        controls_layout.addWidget(self.more_button, alignment=Qt.AlignLeft)
        self.more_panel = QWidget()
        advanced_layout = QHBoxLayout(self.more_panel)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addWidget(QLabel(_("Advanced mode")))
        self.advanced_mode = QComboBox()
        self.advanced_mode.currentIndexChanged.connect(self._set_advanced_mode)
        advanced_layout.addWidget(self.advanced_mode, 1)
        controls_layout.addWidget(self.more_panel)
        self.more_panel.setVisible(self.more_button.isChecked())
        root.addWidget(self.controls_group)

        self.main_tabs = QTabWidget()
        from ui.pages.dynamic_settings import DynamicSettingsPage, SettingsCategory

        self.basic_page = DynamicSettingsPage(self.dbus_handler, SettingsCategory.GENERAL)
        self.shortcuts_page = DynamicSettingsPage(self.dbus_handler, SettingsCategory.SHORTCUTS)
        self.main_tabs.addTab(self._build_basic_tab(), _("Basic"))
        self.main_tabs.addTab(self.shortcuts_page, _("Shortcuts"))
        self.main_tabs.addTab(self._build_system_tab(), _("System"))
        root.addWidget(self.main_tabs, 1)

        actions = QHBoxLayout()
        self.btn_defaults = QPushButton(QIcon.fromTheme("edit-undo"), _("Defaults"))
        self.btn_defaults.clicked.connect(self.on_restore_defaults)
        self.draft_status = QLabel()
        self.draft_status.setObjectName("DraftStatus")
        self.btn_save = QPushButton(QIcon.fromTheme("document-save"), _("Save"))
        self.btn_save.setObjectName("Primary")
        self.btn_save.clicked.connect(self.on_save_all)
        self.btn_close = QPushButton(QIcon.fromTheme("window-close"), _("Close"))
        self.btn_close.clicked.connect(self.close)
        actions.addWidget(self.btn_defaults)
        actions.addWidget(self.draft_status, 1)
        actions.addStretch()
        actions.addWidget(self.btn_close)
        actions.addWidget(self.btn_save)
        root.addLayout(actions)

    def _build_basic_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.basic_page, 1)

        actions = QHBoxLayout()
        macro_button = QPushButton(QIcon.fromTheme("accessories-text-editor"), _("Macro table"))
        macro_button.clicked.connect(self._open_macro_editor)
        actions.addWidget(macro_button)
        self.test_toggle = QPushButton(_("Typing test"))
        self.test_toggle.setCheckable(True)
        actions.addWidget(self.test_toggle)
        actions.addStretch()
        layout.addLayout(actions)

        self.test_group = QGroupBox(_("Typing test"))
        test_layout = QVBoxLayout(self.test_group)
        test_hint = QLabel(_("This field uses your system input method; it does not transform text in Python."))
        test_hint.setWordWrap(True)
        test_layout.addWidget(test_hint)
        test_edit = QPlainTextEdit()
        test_edit.setAccessibleName(_("Typing test"))
        test_edit.setPlaceholderText(_("Type here to test the active input method."))
        test_edit.setMaximumHeight(76)
        test_layout.addWidget(test_edit)
        self.test_toggle.toggled.connect(self.test_group.setVisible)
        self.test_group.setVisible(False)
        layout.addWidget(self.test_group)
        return page

    def _build_system_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        language_group = QGroupBox(_("Language"))
        language_layout = QFormLayout(language_group)
        self.language_selector = QComboBox(language_group)
        self.language_selector.setObjectName("LanguageSelector")
        self.language_selector.setAccessibleName(_("Display language"))
        self.language_selector.addItem(_("System default"), "system")
        self.language_selector.addItem("English", "en")
        self.language_selector.addItem("Tiếng Việt", "vi")
        self.startup_language_preference = str(
            self.ui_settings.value("ui/language", "system") or "system"
        )
        if self.startup_language_preference not in ("system", "en", "vi"):
            self.startup_language_preference = "system"
        self.language_selector.setCurrentIndex(
            self.language_selector.findData(self.startup_language_preference)
        )
        language_layout.addRow(_("Display language"), self.language_selector)
        self.language_selector.currentIndexChanged.connect(
            self._save_language_preference
        )
        layout.addWidget(language_group)

        self.language_restart_note = QLabel(
            _("Reopen Settings to apply the new language.")
        )
        self.language_restart_note.setObjectName("LanguageRestartNote")
        self.language_restart_note.setWordWrap(True)
        self.language_restart_note.setVisible(False)
        layout.addWidget(self.language_restart_note)

        session = os.environ.get("XDG_SESSION_TYPE", "").strip()
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").strip()
        display_backends = []
        if os.environ.get("WAYLAND_DISPLAY", "").strip():
            display_backends.append("Wayland")
        if os.environ.get("DISPLAY", "").strip():
            display_backends.append("X11")

        session_parts = []
        if session:
            session_parts.append(_("Session: {}").format(session))
        elif display_backends:
            session_parts.append(
                _("Available display backends: {}").format(", ".join(display_backends))
            )
        if desktop:
            session_parts.append(_("Desktop: {}").format(desktop))
        session_status = QLabel(" • ".join(session_parts) if session_parts else _("Session information unavailable."))
        session_status.setWordWrap(True)
        layout.addWidget(session_status)

        note = QLabel(
            _("Helper status is context-local and reports the most recent Fcitx input context. It does not guarantee compatibility in every application.")
        )
        note.setWordWrap(True)
        note.setObjectName("DraftStatus")
        layout.addWidget(note)

        groups = [
            (_("Setup"), [
                (_("Activation guide"), self._show_activation_guide),
                (_("Application rules"), self._open_app_rules),
            ]),
            (_("Typing tools"), [
                (_("Advanced settings"), self._open_advanced_settings),
                (_("Custom dictionary"), self._open_dictionary),
                (_("Custom keymap"), self._open_keymap),
            ]),
            (_("Maintenance"), [
                (_("Backup / Restore"), self._open_backup),
                (_("About"), self._open_about),
            ]),
        ]
        for title, actions in groups:
            group = QGroupBox(title)
            group_layout = QHBoxLayout(group)
            for text, action in actions:
                button = QPushButton(text)
                button.clicked.connect(action)
                group_layout.addWidget(button)
            group_layout.addStretch()
            layout.addWidget(group)
        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    def _save_language_preference(self, index):
        language = self.language_selector.itemData(index)
        if language not in ("system", "en", "vi"):
            return
        self.ui_settings.setValue("ui/language", language)
        sync = getattr(self.ui_settings, "sync", None)
        if callable(sync):
            sync()
        self.language_restart_note.setVisible(
            language != self.startup_language_preference
        )

    def _metadata_by_key(self, metadata_list):
        return {
            item[0]: item
            for group in metadata_list
            for item in group[1]
            if len(item) >= 5
        }

    @staticmethod
    def _enum_values(item):
        annotations = item[4]
        values = annotations.get("Enum", {}) if isinstance(annotations, dict) else {}
        return [
            str(values[key])
            for key in sorted(
                values,
                key=lambda key: (0, int(key)) if str(key).isdigit() else (1, str(key)),
            )
        ]

    def _load_controls(self, preserve_draft=False):
        config = self.dbus_handler.get_config()
        if not config:
            self.controls_available = False
            self.controls_group.setEnabled(False)
            self._update_connection_status()
            self.on_changed()
            return

        metadata = self._metadata_by_key(config.get("metadata", []))
        if not all(key in metadata for key in self.CONTROL_KEYS):
            self.controls_available = False
            self.controls_group.setEnabled(False)
            self.dbus_handler.last_error = _("EVKey configuration metadata is incomplete.")
            self._update_connection_status()
            self.on_changed()
            return

        previous_dirty = self.control_dirty.copy() if preserve_draft else {}
        self.controls_available = True
        self.controls_group.setEnabled(True)
        self.control_metadata = metadata
        self.control_values = {
            key: config["values"].get(key, metadata[key][3]) for key in self.CONTROL_KEYS
        }
        self.control_initial_values = self.control_values.copy()
        self.control_dirty = {}
        for key, value in previous_dirty.items():
            self.control_values[key] = value
            if value != self.control_initial_values.get(key):
                self.control_dirty[key] = value
        self._populate_control_widgets()
        self._update_connection_status()

        self.on_changed()

    def _populate_control_widgets(self):
        while self.controls_form.rowCount():
            self.controls_form.removeRow(0)
        self.control_widgets.clear()

        for key in ("OutputCharset", "InputMethod"):
            item = self.control_metadata[key]
            combo = QComboBox()
            values = self._enum_values(item)
            if key == "OutputCharset":
                priority = {
                    value: index for index, value in enumerate(self.OUTPUT_CHARSET_ORDER)
                }
                values.sort(key=lambda value: priority.get(value, len(priority)))
            combo.setMaxVisibleItems(max(1, len(values)))
            for value in values:
                label = self.INPUT_METHOD_LABELS.get(value, value)
                combo.addItem(_(label), value)
            index = combo.findData(str(self.control_values[key]))
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.currentIndexChanged.connect(
                lambda _index, name=key, widget=combo: self._stage_control(name, widget.currentData())
            )
            self.controls_form.addRow(_(item[2]), combo)
            self.control_widgets[key] = combo

        self.advanced_mode.blockSignals(True)
        self.advanced_mode.clear()
        self.advanced_mode.addItem(_("Choose an advanced mode…"), None)
        primary_values = set(self.PRIMARY_MODES)
        for value in self._enum_values(self.control_metadata["Mode"]):
            if value not in primary_values:
                self.advanced_mode.addItem(_(value), value)
        current_mode = str(self.control_values["Mode"])
        advanced_index = self.advanced_mode.findData(current_mode)
        self.advanced_mode.setCurrentIndex(advanced_index if advanced_index >= 0 else 0)
        self.advanced_mode.blockSignals(False)
        self._select_mode_button(current_mode)
        if current_mode not in primary_values and current_mode != "OFF":
            self.more_button.setChecked(True)

    def _select_mode_button(self, mode):
        self.mode_buttons.blockSignals(True)
        button = next(
            (button for button in self.mode_buttons.buttons() if button.property("mode") == mode),
            None,
        )
        if button:
            button.setChecked(True)
        else:
            for candidate in self.mode_buttons.buttons():
                candidate.setChecked(False)
        self.mode_buttons.blockSignals(False)

    def _set_mode(self, mode):
        self.advanced_mode.blockSignals(True)
        self.advanced_mode.setCurrentIndex(0)
        self.advanced_mode.blockSignals(False)
        self._stage_control("Mode", mode)

    def _set_advanced_mode(self, index):
        if index > 0 and self.advanced_mode.currentData() is not None:
            mode = str(self.advanced_mode.currentData())
            self._select_mode_button(mode)
            self._stage_control("Mode", mode)

    def _set_more_expanded(self, expanded):
        self.more_panel.setVisible(expanded)
        self.more_button.setText(_("Fewer modes") if expanded else _("More modes"))
        self.ui_settings.setValue("ui/expanded", expanded)

    def _show_notice(self, title, text):
        message = QLabel(text)
        message.setWordWrap(True)
        message.setPalette(self.palette())
        message.setAutoFillBackground(True)
        self._show_editor(title, message)
    def _toggle_vietnamese(self):
        status = self.dbus_handler.get_fcitx_status()
        if not status:
            self._show_notice(_("Fcitx unavailable"), _("Cannot read Fcitx input state."))
            self._refresh_fcitx_status()
            return
        active = status["current_input_method"] == "evkey" and status["state"] == 2
        if not self.dbus_handler.set_vietnamese_active(not active):
            self._show_notice(
                _("Fcitx unavailable"),
                _("Could not switch EVKey through Fcitx: {}").format(self.dbus_handler.last_status_error),
            )
        self._refresh_fcitx_status()

    def _refresh_fcitx_status(self):
        status = self.dbus_handler.get_fcitx_status()
        keys = self.dbus_handler.get_global_toggle_keys()
        if status is None:
            self.current_input_status.setText(_("Fcitx input state unavailable."))
            self.vietnamese_toggle.setText(_("Turn on Vietnamese"))
            self.vietnamese_toggle.setProperty("active", "false")
            self.vietnamese_toggle.setEnabled(False)
        else:
            current = status["current_input_method"]
            active = current == "evkey" and status["state"] == 2
            state_text = _("EVKey active") if active else _("Current input method: {}").format(current or _("unknown"))
            self.current_input_status.setText(state_text)
            self.vietnamese_toggle.setText(_("Turn off Vietnamese") if active else _("Turn on Vietnamese"))
            self.vietnamese_toggle.setProperty("active", str(active).lower())
            self.vietnamese_toggle.setEnabled(self.controls_available)
            self.vietnamese_toggle.style().unpolish(self.vietnamese_toggle)
            self.vietnamese_toggle.style().polish(self.vietnamese_toggle)

        if keys:
            from ui.components import pretty_format_hotkey_parts

            displayed = [
                " + ".join(pretty_format_hotkey_parts(key)) or key
                for key in keys
            ]
            self.toggle_hotkey_status.setText(_("Toggle shortcut: {}").format(", ".join(displayed)))
        else:
            self.toggle_hotkey_status.setText(_("Toggle shortcut unavailable."))

    def _refresh_runtime_status(self):
        runtime = self.dbus_handler.get_runtime_status()
        if not runtime:
            error = self.dbus_handler.last_status_error
            self.runtime_status.setText(
                _("Could not read EVKey runtime status. Restart Fcitx5 or update EVKey addon.")
                if error
                else _("No recent EVKey input context; helper state unavailable.")
            )
            self.runtime_status.setVisible(bool(error))
            self._fallback_expanded_for = None
            return
        has_context = runtime.get("HasContext", False)
        if not has_context:
            self.runtime_status.setText(_("No recent EVKey input context; helper state unavailable."))
            self.runtime_status.hide()
            self._fallback_expanded_for = None
            return

        requested = str(runtime.get("RequestedMode", ""))
        effective = str(runtime.get("EffectiveMode", ""))
        reason = str(runtime.get("Reason", ""))
        helper_ready = bool(runtime.get("HelperReady", False))
        translated_reasons = {
            "Uinput helper unavailable": _("Uinput helper unavailable"),
            "Helper request exceeds protocol limits": _("Helper request exceeds protocol limits"),
            "Uinput helper request still pending; using Preedit": _("Uinput helper request still pending; using Preedit"),
            "Invalid helper request": _("Invalid helper request"),
            "Uinput helper disconnected; replacement interrupted": _("Uinput helper disconnected; replacement interrupted"),
            "Invalid helper response; replacement interrupted": _("Invalid helper response; replacement interrupted"),
            "Desktop session is inactive or locked": _("Desktop session is inactive or locked"),
            "No supported pointer device detected": _("No supported pointer device detected"),
            "Uinput helper rejected operation": _("Uinput helper rejected operation"),
            "Uinput helper response timed out; replacement interrupted": _("Uinput helper response timed out; replacement interrupted"),
            "Uinput helper disconnected; using Preedit": _("Uinput helper disconnected; using Preedit"),
            "Fake Backspace requires Unicode output": _("Fake Backspace requires Unicode output"),
            "Checking Uinput helper; using Preedit": _("Checking Uinput helper; using Preedit"),
        }
        uinput_modes = {"Uinput (Smooth)", "Uinput (Super Smooth)", "Uinput (Slow)", "Uinput (Select)"}
        if requested in uinput_modes and helper_ready:
            text = _("Recent context: {} is active; Uinput helper ready.").format(_(effective))
        elif reason:
            text = _("Recent context: {} requested, {} effective. {}").format(
                _(requested), _(effective), translated_reasons.get(reason, reason)
            )
        elif requested in uinput_modes:
            text = _("Recent context: checking Uinput helper for {}.").format(_(requested))
        else:
            text = _("Recent context: {} requested, {} effective.").format(_(requested), _(effective))
        self.runtime_status.setText(text)
        self.runtime_status.show()

        fallback_key = (requested, effective, reason)
        if requested in uinput_modes and effective == "Preedit" and reason:
            if fallback_key != self._fallback_expanded_for:
                self.more_button.setChecked(True)
                self._fallback_expanded_for = fallback_key
        else:
            self._fallback_expanded_for = None

    def _open_fcitx_config(self):
        result = QProcess.startDetached("fcitx5-configtool", [])
        started = result[0] if isinstance(result, tuple) else result
        if not started:
            QMessageBox.information(
                self,
                _("Fcitx configuration"),
                _("Run `fcitx5-configtool` to change the input-method toggle shortcut."),
            )

    def _stage_control(self, key, value):
        if value is None or self.control_values.get(key) == value:
            return
        self.control_values[key] = value
        if value == self.control_initial_values.get(key):
            self.control_dirty.pop(key, None)
        else:
            self.control_dirty[key] = value
        self.on_changed()

    def _save_controls(self):
        if not self.control_dirty:
            return True
        config = self.dbus_handler.get_config()
        if not config:
            self._update_connection_status()
            return False
        values = config.get("values", {})
        values.update(self.control_dirty)
        if not self.dbus_handler.set_config(values):
            self._update_connection_status()
            return False
        self.control_initial_values = self.control_values.copy()
        self.control_dirty.clear()
        return True

    def _main_pages(self):
        return (self.basic_page, self.shortcuts_page)

    def _is_modified(self):
        return bool(self.control_dirty) or any(page.is_modified() for page in self._main_pages())

    def on_changed(self):
        modified = self._is_modified()
        valid = not any(
            hasattr(page, "has_validation_errors") and page.has_validation_errors()
            for page in self._main_pages()
        )
        self.btn_save.setEnabled(modified and valid and self.controls_available)
        self.btn_defaults.setEnabled(self.controls_available)
        self.draft_status.setText(_("Unsaved changes") if modified else _("No unsaved changes"))
    def on_restore_defaults(self):
        if not self.controls_available:
            return
        for key in self.CONTROL_KEYS:
            default = self.control_metadata[key][3]
            self._stage_control(key, default)
        self._populate_control_widgets()
        for page in self._main_pages():
            page.restore_defaults()
        self.on_changed()

    def on_save_all(self, quiet=False):
        for page in self._main_pages():
            if hasattr(page, "has_validation_errors") and page.has_validation_errors():
                QMessageBox.warning(self, _("Cannot Save"), page.validation_message())
                return False
        if not self._save_controls():
            QMessageBox.critical(self, _("Error"), _("Failed to save settings. Please check if Fcitx5 is running."))
            return False
        for page in self._main_pages():
            if page.save_data() is False:
                self._update_connection_status()
                QMessageBox.critical(
                    self,
                    _("Error"),
                    _("Failed to save settings. Earlier pages may already have been saved."),
                )
                return False
        self._update_connection_status()
        self.on_changed()
        if not quiet:
            QMessageBox.information(self, _("Success"), _("Settings saved."))
        return True


    def _retry_connection(self):
        self.dbus_handler.reconnect()
        self._load_controls(preserve_draft=True)
        for page in self._main_pages():
            if not page.is_modified():
                page.load_data()
        self._update_connection_status()

    def _poll_connection_status(self):
        if not self.isVisible():
            return
        config = self.dbus_handler.get_config()
        metadata = self._metadata_by_key(config.get("metadata", [])) if config else {}
        available = bool(config) and all(key in metadata for key in self.CONTROL_KEYS)
        if not available:
            self.controls_available = False
            self.controls_group.setEnabled(False)
            if config:
                self.dbus_handler.last_error = _("EVKey configuration metadata is incomplete.")
            self._update_connection_status()
            self.on_changed()
        elif not self.controls_available:
            self._load_controls(preserve_draft=True)
            for page in self._main_pages():
                if not page.is_modified():
                    page.load_data()
        else:
            self._update_connection_status()
        self._refresh_fcitx_status()
        self._refresh_runtime_status()

    def _update_connection_status(self):
        if self.controls_available and self.dbus_handler.last_error:
            text = _("Fcitx5 is available, but an operation failed. Retry to refresh status.")
            connected = False
        elif self.controls_available:
            text = _("Connected to Fcitx5. Changes remain drafts until saved.")
            connected = True
        else:
            error_name = getattr(self.dbus_handler, "last_error_name", "")
            if error_name == "org.freedesktop.DBus.Error.NoReply":
                text = _(
                    "Fcitx5 is not responding. Reconnecting automatically; draft changes are kept."
                )
            elif error_name in {
                "org.freedesktop.DBus.Error.ServiceUnknown",
                "org.freedesktop.DBus.Error.NameHasNoOwner",
                "org.freedesktop.DBus.Error.Disconnected",
            }:
                text = _(
                    "Fcitx5 is unavailable or restarting. Reconnecting automatically; draft changes are kept."
                )
            else:
                text = _(
                    "Fcitx5 did not provide EVKey configuration. Check that the EVKey addon is enabled; draft changes are kept."
                )
            connected = False
        self.connection_status.setText(text)
        self.connection_status.setProperty("connected", str(connected).lower())
        self.connection_status.style().unpolish(self.connection_status)
        self.connection_status.style().polish(self.connection_status)
        self.retry_button.setVisible(not connected)
    def _show_editor(self, title, page):
        was_polling = self.status_timer.isActive()
        self.status_timer.stop()
        try:
            EditorDialog(title, page, self).exec()
        finally:
            if was_polling:
                self.status_timer.start()
            self._update_connection_status()

    def _show_activation_guide(self):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if "GNOME" in desktop:
            desktop_steps = _(
                "GNOME: choose Fcitx5 as the input source in Settings → Keyboard, then add EVKey Linux Community in Fcitx configuration. Qt applications may require the Fcitx Qt input-method module in the desktop session."
            )
        elif "KDE" in desktop or "PLASMA" in desktop:
            desktop_steps = _(
                "KDE Plasma: open System Settings → Keyboard → Virtual Keyboard, choose Fcitx 5, and add EVKey Linux Community in Fcitx configuration."
            )
        elif session_type == "x11":
            desktop_steps = _(
                "X11: select Fcitx5 as the active input method and use XMODIFIERS=@im=fcitx as documented by your distribution. Restart the desktop session after changing environment settings."
            )
        else:
            desktop_steps = _(
                "Choose Fcitx5 as your desktop input method, then add EVKey Linux Community in Fcitx configuration. Desktop setup differs between GNOME, KDE, Wayland and X11."
            )
        helper_steps = _(
            "Optional Smooth helper: install fcitx5-evkey-uinput with your distribution package manager. To opt in, enable it with `sudo systemctl enable --now fcitx5-evkey-server@$(id -u).service`; disable with `sudo systemctl disable --now fcitx5-evkey-server@$(id -u).service`. The helper can emit keys into your login session."
        )
        guide = QLabel()
        guide.setPalette(self.palette())
        guide.setAutoFillBackground(True)
        guide.setWordWrap(True)
        guide.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        guide.setTextInteractionFlags(Qt.TextSelectableByMouse)
        guide.setText(
            desktop_steps + "\n\n" + _("For all desktops:") + " fcitx5-remote -s evkey\n\n" + helper_steps
        )
        self._show_editor(_("Activation guide"), guide)

    def _open_macro_editor(self):
        from ui.pages.macro_editor import MacroEditorPage

        self._show_editor(
            _("Macro table"),
            MacroEditorPage(self.dbus_handler, show_behavior_settings=False),
        )

    def _open_app_rules(self):
        from ui.pages.mode_manager import ModeManagerPage

        self._show_editor(_("Application rules"), ModeManagerPage(self.dbus_handler, show_global_mode=False))

    def _open_advanced_settings(self):
        from ui.pages.dynamic_settings import DynamicSettingsPage, SettingsCategory

        pages = PageGroup(
            [
                (_("Typing"), DynamicSettingsPage(self.dbus_handler, SettingsCategory.TYPING)),
                (_("Appearance"), DynamicSettingsPage(self.dbus_handler, SettingsCategory.APPEARANCE)),
            ]
        )
        self._show_editor(_("Advanced settings"), pages)

    def _open_dictionary(self):
        from ui.pages.dict_editor import DictEditorPage

        self._show_editor(_("Custom dictionary"), DictEditorPage(self.dbus_handler))

    def _open_keymap(self):
        from ui.pages.keymap_editor import KeymapEditorPage

        self._show_editor(_("Custom keymap"), KeymapEditorPage(self.dbus_handler))

    def _open_backup(self):
        from ui.pages.backup import BackupPage

        self._show_editor(_("Backup / Restore"), BackupPage(self.dbus_handler))

    def _open_about(self):
        from ui.pages.about import AboutPage

        self._show_editor(_("About"), AboutPage())

    def closeEvent(self, event):
        if not self._is_modified():
            event.accept()
            return
        answer = QMessageBox.question(
            self,
            _("Save Changes"),
            _("Save changes before closing?"),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if answer == QMessageBox.Save:
            if self.on_save_all(quiet=True):
                event.accept()
            else:
                event.ignore()
        elif answer == QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()

    def _setup_window_size(self):
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else self.geometry()
        width = min(760, available.width())
        height = min(620, available.height())
        self.setMinimumSize(640, 500)
        self.resize(width, height)
        if screen:
            self.move(
                available.x() + (available.width() - width) // 2,
                available.y() + (available.height() - height) // 2,
            )
