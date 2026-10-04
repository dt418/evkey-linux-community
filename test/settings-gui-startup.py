import copy
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import dbus
from qtpy.QtCore import QPoint, QRect, QTimer
from qtpy.QtGui import QPalette
from qtpy.QtWidgets import QApplication, QDialogButtonBox, QGridLayout, QLabel, QScrollArea
from qtpy.QtWidgets import QMessageBox
from qtpy.QtWidgets import QComboBox
from qtpy.QtWidgets import QPushButton
from i18n import _, setup_i18n
from core.dbus_handler import LotusDBusHandler
from ui.main_window import EditorDialog, LotusSettingsWindow, PageGroup
from ui.pages.about import AboutPage
from ui.pages.dynamic_settings import DynamicSettingsPage, SettingsCategory

INPUT_METHOD_NAMES = (
    "Telex",
    "VNI",
    "Telex + VNI",
    "Telex + VNI + VIQR",
    "VIQR",
    "Microsoft layout",
    "VNI Bàn phím tiếng Pháp",
    "Custom",
)
OUTPUT_CHARSETS = (
    "Unicode",
    "BKHCM 1",
    "BKHCM 2",
    "NCR Decimal",
    "NCR Hex",
    "TCVN3 (ABC)",
    "Unicode C string Decimal",
    "Unicode C string Hex",
    "Unicode tổ hợp",
    "UTF-8",
    "Vietware Full",
    "Vietware X",
    "VIQR",
    "VISCII",
    "VNI Windows",
    "VPS",
    "Windows 1258 codepage",
)
OUTPUT_CHARSET_DISPLAY_ORDER = (
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

CONFIG = {
    "values": {
        "InputMethod": "Telex",
        "OutputCharset": "Unicode",
        "Mode": "Uinput",
        "ModernStyle": True,
        "FreeMarking": True,
        "SpellCheck": True,
        "AutoNonVnRestore": True,
        "AutoCapitalizeAfterPunctuation": False,
        "EnableMacro": True,
        "EnableMacroInOffMode": False,
    },
    "metadata": [
        [
            "EVKey",
            [
                [
                    "InputMethod",
                    "Enum",
                    "Input method",
                    "Telex",
                    {"Enum": {str(index): value for index, value in enumerate(INPUT_METHOD_NAMES)}},
                ],
                [
                    "OutputCharset",
                    "Enum",
                    "Output charset",
                    "Unicode",
                    {"Enum": {str(index): value for index, value in enumerate(OUTPUT_CHARSETS)}},
                ],
                [
                    "Mode",
                    "Enum",
                    "Mode",
                    "Preedit",
                    {"Enum": {"0": "Preedit", "1": "Fake Backspace", "2": "Uinput (Smooth)", "3": "Uinput"}},
                ],
                *[
                    [key, "Boolean", key, default, {}]
                    for key, default in (
                        ("ModernStyle", True),
                        ("FreeMarking", True),
                        ("SpellCheck", True),
                        ("AutoNonVnRestore", True),
                        ("AutoCapitalizeAfterPunctuation", False),
                        ("EnableMacro", True),
                        ("EnableMacroInOffMode", False),
                    )
                ],
            ],
        ]
    ],
}


class FakeController:
    def __init__(self):
        self.current_input_method = "keyboard-us"
        self.state = 1
        self.config_uris = []
        self.calls = []

    def GetConfig(self, uri, **_kwargs):
        self.config_uris.append(uri)
        if uri.endswith("/runtime"):
            return (
                {"HasContext": True, "RequestedMode": "Uinput (Smooth)"},
                {},
            )
        if uri == "fcitx://config/global":
            return ({"Hotkey": {"TriggerKeys": ["Control+space"]}}, {})
        return ({}, {})

    def CurrentInputMethod(self, **_kwargs):
        return self.current_input_method

    def State(self, **_kwargs):
        return self.state

    def SetCurrentIM(self, name, **_kwargs):
        self.calls.append(("SetCurrentIM", name))
        self.current_input_method = name

    def Activate(self, **_kwargs):
        self.calls.append(("Activate",))
        self.state = 2

    def Deactivate(self, **_kwargs):
        self.calls.append(("Deactivate",))
        self.state = 1

    def SetConfig(self, *_args, **_kwargs):
        self.calls.append(("SetConfig",))



class FakeSettings:
    values = {}

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        return type(value) if type is not None else value

    def setValue(self, key, value):
        self.values[key] = value


class FakeDBusHandler:
    def __init__(self):
        self.last_error = ""
        self.last_error_name = ""
        self.last_status_error = ""
        self.state = 1
        self.current_input_method = "keyboard-us"
        self.runtime_status = {"HasContext": False}
        self.activation_requests = []
        self.available = True

    def get_config(self):
        return copy.deepcopy(CONFIG) if self.available else {}
    def get_runtime_status(self):
        return copy.deepcopy(self.runtime_status)

    def get_global_toggle_keys(self):
        return ["Control+space"]

    def get_fcitx_status(self):
        return {
            "current_input_method": self.current_input_method,
            "state": self.state,
        }

    def set_vietnamese_active(self, active):
        self.activation_requests.append(active)
        self.current_input_method = "evkey" if active else self.current_input_method
        self.state = 2 if active else 1
        return True

    def set_config(self, _values):
        return True

    def reconnect(self):
        self.available = True
        return True


class SettingsLanguageTest(unittest.TestCase):
    def test_system_default_uses_system_locale(self):
        self.addCleanup(setup_i18n, "system")
        with patch.dict(os.environ, {"LC_ALL": "C", "LANGUAGE": ""}):
            setup_i18n("system")
            self.assertEqual(_("Basic"), "Basic")

    def test_english_override_uses_source_strings(self):
        self.addCleanup(setup_i18n, "system")
        setup_i18n("vi")
        setup_i18n("en")
        self.assertEqual(_("Basic"), "Basic")

    def test_system_default_uses_detected_system_language_catalog(self):
        catalog = "/usr/share/locale/vi/LC_MESSAGES/fcitx5-evkey.mo"
        if not os.path.isfile(catalog):
            self.skipTest("Vietnamese application catalog is not installed")
        self.addCleanup(setup_i18n, "system")
        with patch.dict(
            os.environ,
            {
                "LANGUAGE": "vi",
                "LC_ALL": "",
                "LC_MESSAGES": "",
                "LANG": "C.UTF-8",
            },
        ):
            setup_i18n("system")
        self.assertEqual(_("Basic"), "Cơ bản")

    def test_vietnamese_override_uses_installed_catalog(self):
        catalog = "/usr/share/locale/vi/LC_MESSAGES/fcitx5-evkey.mo"
        if not os.path.isfile(catalog):
            self.skipTest("Vietnamese application catalog is not installed")
        self.addCleanup(setup_i18n, "system")
        setup_i18n("vi")
        self.assertEqual(_("Basic"), "Cơ bản")

class DBusReadOnlyStatusTest(unittest.TestCase):
    def test_status_reads_are_read_only_and_activation_uses_controller(self):
        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = FakeController()
        handler.last_error = ""
        handler.last_status_error = ""

        runtime = handler.get_runtime_status()
        self.assertTrue(runtime["HasContext"])
        self.assertEqual(handler.get_global_toggle_keys(), ["Control+space"])
        self.assertEqual(
            handler.iface.config_uris,
            [
                "fcitx://config/addon/evkey/runtime",
                "fcitx://config/global",
            ],
        )
        self.assertTrue(handler.set_vietnamese_active(True))
        self.assertEqual(
            handler.iface.calls,
            [("SetCurrentIM", "evkey"), ("Activate",)],
        )
        self.assertTrue(handler.set_vietnamese_active(False))
        self.assertEqual(handler.iface.calls[-1], ("Deactivate",))
        self.assertNotIn(("SetConfig",), handler.iface.calls)


    def test_activation_reports_success_only_when_fcitx_changes_state(self):
        class NoOpController:
            def CurrentInputMethod(self, **_kwargs):
                return "keyboard-us"

            def State(self, **_kwargs):
                return 1

            def SetCurrentIM(self, _name, **_kwargs):
                pass

            def Activate(self, **_kwargs):
                pass

        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = NoOpController()
        handler.last_status_error = ""

        self.assertFalse(handler.set_vietnamese_active(True))
        self.assertIn("did not apply", handler.last_status_error)

    def test_runtime_status_recovers_after_fcitx_owner_changes(self):
        class StaleController:
            def GetConfig(self, _uri, **_kwargs):
                raise dbus.DBusException(
                    "Fcitx5 owner disappeared",
                    name="org.freedesktop.DBus.Error.ServiceUnknown",
                )

        class RecoveredController:
            def GetConfig(self, _uri, **_kwargs):
                return {"HasContext": True}, {}

        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = StaleController()
        handler.last_error = ""
        handler.last_error_name = ""
        handler.last_status_error = ""
        handler._auto_retry_at = 0.0
        handler._auto_retry_delay = 1.0

        def reconnect():
            handler.iface = RecoveredController()
            return True

        with patch.object(handler, "reconnect", side_effect=reconnect) as reconnect_mock:
            self.assertEqual(handler.get_runtime_status(), {"HasContext": True})
        reconnect_mock.assert_called_once_with()
        self.assertEqual(handler.last_error, "")

    def test_subconfig_read_recovers_after_fcitx_owner_changes(self):
        class StaleController:
            def GetConfig(self, _uri, **_kwargs):
                raise dbus.DBusException(
                    "Fcitx5 owner disappeared",
                    name="org.freedesktop.DBus.Error.NameHasNoOwner",
                )

        class RecoveredController:
            def GetConfig(self, _uri, **_kwargs):
                return {"Rules": {"0": {"Program": "app", "Mode": 9}}}, {}

        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = StaleController()
        handler.last_error = ""
        handler.last_error_name = ""
        handler._auto_retry_at = 0.0
        handler._auto_retry_delay = 1.0

        def reconnect():
            handler.iface = RecoveredController()
            return True

        with patch.object(handler, "reconnect", side_effect=reconnect) as reconnect_mock:
            self.assertEqual(
                handler.get_sub_config_list("app_rules", "Rules"),
                [{"Program": "app", "Mode": 9}],
            )
        reconnect_mock.assert_called_once_with()
        self.assertEqual(handler.last_error, "")

    def test_ambiguous_write_failure_invalidates_connection_without_retry(self):
        class UnresponsiveController:
            def __init__(self):
                self.calls = 0

            def SetConfig(self, *_args, **_kwargs):
                self.calls += 1
                raise dbus.DBusException(
                    "Fcitx5 did not reply",
                    name="org.freedesktop.DBus.Error.NoReply",
                )

        controller = UnresponsiveController()
        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = controller
        handler.last_error = ""
        handler.last_error_name = ""
        handler._auto_retry_at = 0.0
        handler._auto_retry_delay = 1.0

        with patch.object(handler, "reconnect") as reconnect_mock:
            self.assertFalse(handler.set_config({"Mode": 9}))

        self.assertEqual(controller.calls, 1)
        self.assertIsNone(handler.iface)
        reconnect_mock.assert_not_called()
        self.assertEqual(
            handler.last_error_name,
            "org.freedesktop.DBus.Error.NoReply",
        )
        self.assertTrue(handler.last_error)

    def test_get_config_reconnects_after_fcitx_owner_disappears(self):
        class StaleController:
            def GetConfig(self, _uri, **_kwargs):
                raise dbus.DBusException(
                    "The name :1.78 was not provided by any service files",
                    name="org.freedesktop.DBus.Error.ServiceUnknown",
                )

        class RecoveredController:
            def GetConfig(self, _uri, **_kwargs):
                return CONFIG["values"], CONFIG["metadata"]

        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = StaleController()
        handler._auto_retry_at = 0.0
        handler.bus = None
        handler._last_owner = None

        def reconnect():
            handler.iface = RecoveredController()
            return True

        with patch.object(handler, "reconnect", side_effect=reconnect) as reconnect_mock:
            self.assertEqual(handler.get_config(), CONFIG)

    def test_disconnected_service_retries_with_backoff(self):
        class StaleController:
            def GetConfig(self, _uri, **_kwargs):
                raise dbus.DBusException(
                    "The name :1.78 was not provided by any service files",
                    name="org.freedesktop.DBus.Error.ServiceUnknown",
                )

        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = StaleController()
        handler.last_error = ""
        handler.bus = None
        handler._last_owner = None
        handler._auto_retry_at = 0.0
        handler._auto_retry_delay = 1.0

        def reconnect():
            handler.iface = StaleController()
            return True

        with (
            patch.object(handler, "reconnect", side_effect=reconnect) as reconnect_mock,
            patch("core.dbus_handler.time.monotonic", return_value=10.0),
        ):
            self.assertEqual(handler.get_config(), {})
        reconnect_mock.assert_called_once_with()
        self.assertIsNone(handler.iface)
        self.assertEqual(handler._auto_retry_at, 11.0)

        with (
            patch.object(handler, "reconnect", side_effect=reconnect) as reconnect_mock,
            patch("core.dbus_handler.time.monotonic", return_value=10.5),
        ):
            self.assertEqual(handler.get_config(), {})
        reconnect_mock.assert_not_called()

    def test_config_reconnects_immediately_when_fcitx_owner_returns(self):
        class OwnerBus:
            def get_name_owner(self, _name):
                return "present"

        class RecoveredController:
            def GetConfig(self, _uri, **_kwargs):
                return CONFIG["values"], CONFIG["metadata"]

        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.bus = OwnerBus()
        handler.iface = None
        handler.last_error = ""
        handler.last_error_name = ""
        handler._last_owner = None
        handler._auto_retry_at = 100.0
        handler._auto_retry_delay = 30.0
        def reconnect():
            handler.iface = RecoveredController()
            return True

        with (
            patch.object(handler, "reconnect", side_effect=reconnect) as reconnect_mock,
            patch("core.dbus_handler.time.monotonic", return_value=1.0),
        ):
            self.assertEqual(handler.get_config(), CONFIG)
        reconnect_mock.assert_called_once_with()

    def test_no_reply_does_not_block_on_immediate_retry(self):
        class UnresponsiveController:
            def __init__(self):
                self.calls = 0
                self.timeout = None

            def GetConfig(self, _uri, **kwargs):
                self.calls += 1
                self.timeout = kwargs.get("timeout")
                raise dbus.DBusException(
                    "Fcitx5 did not reply",
                    name="org.freedesktop.DBus.Error.NoReply",
                )

        controller = UnresponsiveController()
        handler = LotusDBusHandler.__new__(LotusDBusHandler)
        handler.addon_name = "fcitx://config/addon/evkey"
        handler.iface = controller
        handler.last_error = ""
        handler._auto_retry_at = 0.0
        handler._auto_retry_delay = 1.0

        with patch.object(handler, "reconnect") as reconnect_mock:
            self.assertEqual(handler.get_config(), {})

        self.assertEqual(controller.calls, 1)
        self.assertEqual(controller.timeout, 2.0)
        self.assertIsNone(handler.iface)
        reconnect_mock.assert_not_called()


class SettingsWindowStartupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _window(self, preserve_settings=False):
        if not preserve_settings:
            FakeSettings.values.clear()
        with patch("ui.main_window.LotusDBusHandler", FakeDBusHandler):
            with patch("ui.main_window.QSettings", FakeSettings):
                return LotusSettingsWindow()

    def test_window_loads_controls_and_advanced_mode(self):
        window = self._window()
        self.addCleanup(window.close)
        self.assertTrue(window.controls_available)
        self.assertGreater(window.control_widgets["InputMethod"].count(), 0)
        for key, names in (
            ("InputMethod", INPUT_METHOD_NAMES),
            ("OutputCharset", OUTPUT_CHARSETS),
        ):
            combo = window.control_widgets[key]
            actual = [combo.itemData(index) for index in range(combo.count())]
            self.assertCountEqual(actual, names)
            if key == "OutputCharset":
                self.assertEqual(actual, list(OUTPUT_CHARSET_DISPLAY_ORDER))
            self.assertEqual(combo.maxVisibleItems(), len(names))
        self.assertEqual(window.advanced_mode.currentData(), "Uinput")
        self.assertEqual(window.advanced_mode.itemText(0), "Choose an advanced mode…")
        self.assertTrue(window.more_button.isChecked())
        self.assertTrue(window.retry_button.isHidden())
        self.assertIn("Toggle shortcut", window.toggle_hotkey_status.text())


    def test_language_preference_defaults_to_system_and_persists_override(self):
        window = self._window()
        self.addCleanup(window.close)
        selector = window.findChild(QComboBox, "LanguageSelector")
        self.assertIsNotNone(selector)
        self.assertEqual(
            [selector.itemData(index) for index in range(selector.count())],
            ["system", "en", "vi"],
        )
        self.assertEqual(selector.currentData(), "system")

        selector.setCurrentIndex(selector.findData("vi"))
        self.assertEqual(FakeSettings.values.get("ui/language"), "vi")
        restart_note = window.findChild(QLabel, "LanguageRestartNote")
        self.assertIsNotNone(restart_note)
        self.assertFalse(restart_note.isHidden())

        reopened = self._window(preserve_settings=True)
        self.addCleanup(reopened.close)
        reopened_selector = reopened.findChild(QComboBox, "LanguageSelector")
        self.assertEqual(reopened_selector.currentData(), "vi")

    def test_basic_options_use_two_columns(self):
        window = self._window()
        self.addCleanup(window.close)
        grids = window.basic_page.findChildren(QGridLayout)
        self.assertEqual(sorted(grid.count() for grid in grids), [2, 5])
        typing_grid = next(grid for grid in grids if grid.count() == 5)
        self.assertEqual(
            [typing_grid.getItemPosition(index)[:2] for index in range(5)],
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],
        )


    def test_retry_visibility_tracks_connection(self):
        window = self._window()
        self.addCleanup(window.close)
        window.show()
        self.app.processEvents()
        window.dbus_handler.available = False
        window._poll_connection_status()
        self.assertIn("EVKey configuration", window.connection_status.text())
        window.dbus_handler.last_error = "raw D-Bus detail"
        window.dbus_handler.last_error_name = "org.freedesktop.DBus.Error.NoReply"
        window._update_connection_status()
        self.assertIn("not responding", window.connection_status.text())
        self.assertNotIn("raw D-Bus detail", window.connection_status.text())
        window.dbus_handler.last_error = ""
        window.dbus_handler.last_error_name = ""
        self.assertFalse(window.retry_button.isHidden())
        self.assertFalse(window.controls_group.isEnabled())
        window.retry_button.click()
        self.assertTrue(window.retry_button.isHidden())
        self.assertTrue(window.controls_group.isEnabled())

    def test_tabs_reload_after_fcitx_returns_from_unavailable_startup(self):
        with patch.object(FakeDBusHandler, "get_config", return_value={}):
            window = self._window()
        self.addCleanup(window.close)
        window.show()
        self.app.processEvents()
        self.assertFalse(window.controls_available)
        self.assertFalse(window.basic_page.current_values)
        self.assertFalse(window.shortcuts_page.current_values)

        window._poll_connection_status()
        self.app.processEvents()

        self.assertTrue(window.controls_available)
        self.assertEqual(window.basic_page.current_values, CONFIG["values"])
        self.assertEqual(window.shortcuts_page.current_values, CONFIG["values"])
        scrollbar = window.basic_page.scroll.verticalScrollBar()
        self.assertGreater(scrollbar.maximum(), 0)
        self.assertTrue(scrollbar.isVisible())
        stale_messages = [
            label
            for page in window._main_pages()
            for label in page.findChildren(QLabel)
            if label.text() == "Failed to load configuration." and label.isVisible()
        ]
        self.assertEqual(stale_messages, [])

    def test_automatic_recovery_keeps_unsaved_page_changes(self):
        window = self._window()
        self.addCleanup(window.close)
        self.addCleanup(window.basic_page.load_data)
        window.show()
        draft = not window.basic_page.current_values["SpellCheck"]
        window.basic_page.update_config("SpellCheck", draft)
        window.dbus_handler.available = False
        window._poll_connection_status()
        window.dbus_handler.available = True

        window._poll_connection_status()

        self.assertTrue(window.controls_available)
        self.assertEqual(window.basic_page.current_values["SpellCheck"], draft)
        self.assertEqual(window.basic_page.modified_values["SpellCheck"], draft)
        self.assertTrue(window.basic_page.is_modified())

    def test_advanced_expansion_preference_persists(self):
        original_mode = CONFIG["values"]["Mode"]
        CONFIG["values"]["Mode"] = "Preedit"
        self.addCleanup(CONFIG["values"].__setitem__, "Mode", original_mode)
        window = self._window()
        self.addCleanup(window.close)
        window.more_button.setChecked(False)
        restored = self._window(preserve_settings=True)
        self.addCleanup(restored.close)
        self.assertFalse(restored.more_button.isChecked())
    def test_toggle_uses_fcitx_input_method_state(self):
        window = self._window()
        self.addCleanup(window.close)
        window.vietnamese_toggle.click()
        self.assertEqual(window.dbus_handler.activation_requests, [True])
        self.assertEqual(window.vietnamese_toggle.text(), "Turn off Vietnamese")


    def test_toggle_reports_fcitx_noop_in_palette_aware_dialog(self):
        window = self._window()
        self.addCleanup(window.close)
        window.dbus_handler.last_status_error = "Fcitx did not apply the requested EVKey state."
        window.dbus_handler.set_vietnamese_active = lambda _active: False
        dialogs = []

        def close_notice():
            dialog = window.findChild(EditorDialog)
            self.assertIsNotNone(dialog)
            self.assertFalse(window.status_timer.isActive())
            dialogs.append(dialog)
            dialog.accept()

        QTimer.singleShot(0, close_notice)
        window._toggle_vietnamese()

        self.assertIn("did not apply", dialogs[0].page.text())
        self.assertTrue(window.status_timer.isActive())
        self.assertEqual(
            dialogs[0].page.palette().color(QPalette.Window),
            window.palette().color(QPalette.Window),
        )

    def test_runtime_status_error_uses_actionable_guidance(self):
        window = self._window()
        self.addCleanup(window.close)
        window.dbus_handler.runtime_status = {}
        window.dbus_handler.last_status_error = "raw D-Bus detail"

        window._refresh_runtime_status()

        self.assertIn("Restart Fcitx5 or update EVKey addon", window.runtime_status.text())
        self.assertNotIn("raw D-Bus detail", window.runtime_status.text())
    def test_recent_helper_fallback_expands_advanced_modes(self):
        window = self._window()
        self.addCleanup(window.close)
        window.more_button.setChecked(False)
        window.dbus_handler.runtime_status = {
            "HasContext": True,
            "RequestedMode": "Uinput (Smooth)",
            "EffectiveMode": "Preedit",
            "Reason": "Uinput helper unavailable",
            "HelperReady": False,
        }
        window._refresh_runtime_status()
        self.assertTrue(window.more_button.isChecked())
        self.assertIn("Uinput helper unavailable", window.runtime_status.text())
        self.assertIn("Preedit", window.runtime_status.text())

    def test_system_tab_reports_available_displays_without_session_metadata(self):
        environment = {
            "XDG_SESSION_TYPE": "",
            "XDG_CURRENT_DESKTOP": "",
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": ":0",
        }
        with patch.dict(os.environ, environment):
            window = self._window()
        self.addCleanup(window.close)

        labels = window.main_tabs.widget(2).findChildren(QLabel)
        self.assertTrue(
            any("Wayland" in label.text() and "X11" in label.text() for label in labels)
        )


    def test_activation_guide_opens_native_dialog(self):
        window = self._window()
        self.addCleanup(window.close)
        environment = {"XDG_CURRENT_DESKTOP": "", "XDG_SESSION_TYPE": "x11"}
        dialog = []

        def close_guide():
            guide = window.findChild(EditorDialog)
            self.assertIsNotNone(guide)
            dialog.append(guide)
            guide.accept()

        with patch.dict(os.environ, environment):
            QTimer.singleShot(0, close_guide)
            window._show_activation_guide()

        guide = dialog[0]
        self.assertEqual(guide.windowTitle(), _("Activation guide"))
        self.assertIsInstance(guide.page, QLabel)
        self.assertTrue(guide.page.wordWrap())
        self.assertIn("\n\nFor all desktops:", guide.page.text())
        self.assertNotIn("\\n", guide.page.text())
        self.assertTrue(guide.page.autoFillBackground())
        self.assertEqual(
            guide.page.palette().color(QPalette.Window),
            window.palette().color(QPalette.Window),
        )
        self.assertIsNotNone(guide.buttons.button(QDialogButtonBox.Close))

    def test_close_uses_visible_discard_confirmation_on_first_click(self):
        page = QLabel("Draft")
        page.is_modified = lambda: True
        dialog = EditorDialog("Editor", page)
        confirmation = []

        def click_close():
            dialog.buttons.button(QDialogButtonBox.Close).click()

        def dismiss_confirmation():
            prompts = [
                widget
                for widget in QApplication.topLevelWidgets()
                if widget is not dialog and widget.isVisible()
            ]
            if not prompts:
                dialog.reject()
                return
            prompt = prompts[0]
            confirmation.append(prompt)
            if isinstance(prompt, QMessageBox):
                prompt.done(QMessageBox.Discard)
            else:
                prompt.findChild(QDialogButtonBox).button(QDialogButtonBox.Discard).click()

        QTimer.singleShot(0, click_close)
        QTimer.singleShot(0, dismiss_confirmation)
        dialog.exec()

        self.assertEqual(len(confirmation), 1)
        self.assertNotIsInstance(confirmation[0], QMessageBox)
        self.assertEqual(confirmation[0].windowTitle(), _("Discard Changes"))
        self.assertFalse(dialog.isVisible())

    def test_advanced_editor_keeps_save_and_close_controls_visible(self):
        dbus_handler = FakeDBusHandler()
        pages = PageGroup(
            [
                (
                    "Typing",
                    DynamicSettingsPage(dbus_handler, SettingsCategory.TYPING),
                ),
                (
                    "Appearance",
                    DynamicSettingsPage(dbus_handler, SettingsCategory.APPEARANCE),
                ),
            ]
        )
        dialog = EditorDialog("Advanced settings", pages)
        dialog.show()
        self.app.processEvents()
        self.addCleanup(dialog.close)

        for role in (QDialogButtonBox.Save, QDialogButtonBox.Close):
            button = dialog.buttons.button(role)
            self.assertIsNotNone(button)
            self.assertTrue(button.isVisible())
            button_rect = QRect(button.mapTo(dialog, QPoint(0, 0)), button.size())
            self.assertTrue(dialog.rect().contains(button_rect))

    def test_system_actions_remain_reachable_when_more_modes_expand(self):
        window = self._window()
        self.addCleanup(window.close)
        window.resize(720, 520)
        window.more_button.setChecked(True)
        window.show()
        window.main_tabs.setCurrentIndex(2)
        self.app.processEvents()

        page = window.main_tabs.widget(2)
        self.assertIsInstance(page, QScrollArea)
        scrollbar = page.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.app.processEvents()
        about_button = next(
            button for button in page.findChildren(QPushButton) if button.text() == "About"
        )
        button_rect = QRect(
            about_button.mapTo(page, QPoint(0, 0)),
            about_button.size(),
        )
        self.assertTrue(page.rect().contains(button_rect))

    def test_about_licenses_remain_reachable_in_compact_dialog(self):
        dialog = EditorDialog("About", AboutPage())
        dialog.resize(480, 360)
        dialog.show()
        self.app.processEvents()
        self.addCleanup(dialog.close)

        self.assertIsNone(dialog.buttons.button(QDialogButtonBox.Save))
        close_button = dialog.buttons.button(QDialogButtonBox.Close)
        self.assertIsNotNone(close_button)
        self.assertTrue(close_button.isVisible())
        license_labels = dialog.findChildren(QLabel)
        license_labels = [
            label
            for label in license_labels
            if label.objectName() in ("MainLicenseInfo", "ThirdPartyLicenseInfo")
        ]
        self.assertEqual(len(license_labels), 2)
        for label in license_labels:
            self.assertTrue(label.hasHeightForWidth())
            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))

        scroll = dialog.findChild(QScrollArea, "AboutScrollArea")
        license_info = dialog.findChild(QLabel, "ThirdPartyLicenseInfo")
        self.assertIsNotNone(scroll)
        self.assertIsNotNone(license_info)

        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        self.app.processEvents()
        license_rect = QRect(
            license_info.mapTo(scroll.viewport(), QPoint(0, 0)),
            license_info.size(),
        )
        self.assertTrue(scroll.viewport().rect().contains(license_rect))


if __name__ == "__main__":
    unittest.main()
