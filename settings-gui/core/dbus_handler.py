# SPDX-FileCopyrightText: 2026 Nguyen Hoang Ky <nhktmdzhg@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
D-Bus handler to communicate with Fcitx5 Controller.
"""

import time

import dbus


DBUS_TIMEOUT_SECONDS = 2.0
FCITX_SERVICE = "org.fcitx.Fcitx5"
NO_REPLY_ERROR = "org.freedesktop.DBus.Error.NoReply"

CONNECTION_ERRORS = {
    "org.freedesktop.DBus.Error.ServiceUnknown",
    "org.freedesktop.DBus.Error.NameHasNoOwner",
    "org.freedesktop.DBus.Error.Disconnected",
}

RETRYABLE_OWNER_ERRORS = {
    "org.freedesktop.DBus.Error.ServiceUnknown",
    "org.freedesktop.DBus.Error.NameHasNoOwner",
}


class LotusDBusHandler:
    """Fcitx5 configuration client for EVKey Linux Community."""

    def __init__(self):
        self.addon_name = "fcitx://config/addon/evkey"
        self.bus = None
        self.proxy = None
        self.iface = None
        self.last_error = ""
        self.last_error_name = ""
        self.last_status_error = ""
        self._last_owner = None
        self._auto_retry_at = 0.0
        self._auto_retry_delay = 1.0
        self.reconnect()

    @property
    def is_connected(self) -> bool:
        return self.iface is not None

    def reconnect(self) -> bool:
        """Reconnect without discarding caller-owned draft state."""
        self.bus = None
        self.proxy = None
        self.iface = None
        try:
            self.bus = dbus.SessionBus()
            self.proxy = self.bus.get_object(FCITX_SERVICE, "/controller")
            self.iface = dbus.Interface(self.proxy, "org.fcitx.Fcitx.Controller1")
            try:
                self._last_owner = self.bus.get_name_owner(FCITX_SERVICE)
            except dbus.DBusException:
                self._last_owner = None
            self.last_error = ""
            self.last_error_name = ""
            return True
        except dbus.DBusException as e:
            self.last_error = str(e)
            self.last_error_name = e.get_dbus_name() or ""
            return False

    def _service_owner_returned(self) -> bool:
        if self.bus is None:
            return False
        try:
            owner = self.bus.get_name_owner(FCITX_SERVICE)
        except dbus.DBusException as e:
            self._last_owner = None
            return (
                e.get_dbus_name()
                == "org.freedesktop.DBus.Error.Disconnected"
            )
        if owner == self._last_owner:
            return False
        self._last_owner = owner
        return owner is not None

    def get_config(self) -> dict:
        """Read configuration and recover from a vanished Fcitx service owner."""
        if not self.iface:
            if time.monotonic() < self._auto_retry_at:
                if not self._service_owner_returned():
                    return {}
                self._auto_retry_at = 0.0
                self._auto_retry_delay = 1.0
            if not self.reconnect():
                self._schedule_auto_retry()
                return {}
        try:
            return self._read_config()
        except dbus.DBusException as e:
            self.last_error = str(e)
            self.last_error_name = e.get_dbus_name() or ""
            if self.last_error_name == NO_REPLY_ERROR:
                self.iface = None
                self._schedule_auto_retry()
                return {}
            if self.last_error_name not in CONNECTION_ERRORS:
                return {}
            if not self.reconnect():
                self._schedule_auto_retry()
                return {}
            try:
                return self._read_config()
            except Exception as retry_error:
                self.last_error = str(retry_error)
                self.last_error_name = (
                    retry_error.get_dbus_name() or ""
                    if isinstance(retry_error, dbus.DBusException)
                    else ""
                )
                if (
                    isinstance(retry_error, dbus.DBusException)
                    and retry_error.get_dbus_name() in CONNECTION_ERRORS
                ):
                    self.iface = None
                    self._schedule_auto_retry()
                return {}
        except Exception as e:
            self.last_error = str(e)
            self.last_error_name = ""
            return {}

    def _schedule_auto_retry(self):
        self._auto_retry_at = time.monotonic() + self._auto_retry_delay
        self._auto_retry_delay = min(self._auto_retry_delay * 2, 30.0)

    def _remember_controller_error(self, error):
        self.last_error = str(error)
        self.last_error_name = error.get_dbus_name() or ""
        if (
            self.last_error_name in CONNECTION_ERRORS
            or self.last_error_name == NO_REPLY_ERROR
        ):
            self.iface = None
            self.proxy = None
            self._schedule_auto_retry()

    def _clear_controller_error(self):
        self.last_error = ""
        self.last_error_name = ""
        self.last_status_error = ""
        self._auto_retry_at = 0.0
        self._auto_retry_delay = 1.0

    def _call_controller(
        self,
        method_name,
        *args,
        retry_owner_loss=False,
        **kwargs,
    ):
        """Retry once only for reads when D-Bus confirms no owner handled the call."""
        try:
            result = getattr(self.iface, method_name)(*args, **kwargs)
        except dbus.DBusException as error:
            error_name = error.get_dbus_name() or ""
            self._remember_controller_error(error)
            if (
                not retry_owner_loss
                or error_name not in RETRYABLE_OWNER_ERRORS
                or not self.reconnect()
            ):
                raise
            try:
                result = getattr(self.iface, method_name)(*args, **kwargs)
            except dbus.DBusException as retry_error:
                self._remember_controller_error(retry_error)
                raise
        self._clear_controller_error()
        return result

    def _read_config(self) -> dict:
        values, metadata = self.iface.GetConfig(
            self.addon_name,
            timeout=DBUS_TIMEOUT_SECONDS,
        )
        self.last_error = ""
        self.last_error_name = ""
        self._auto_retry_at = 0.0
        self._auto_retry_delay = 1.0
        return {
            "values": self._clean_dbus(values),
            "metadata": self._clean_dbus(metadata),
        }

    def get_runtime_status(self) -> dict:
        """Read EVKey's non-persistent status snapshot for the recent context."""
        return self._get_readonly_config(f"{self.addon_name}/runtime")

    def get_global_toggle_keys(self) -> list:
        """Read Fcitx's configured input-method toggle keys without changing them."""
        config = self._get_readonly_config("fcitx://config/global")
        hotkeys = config.get("Hotkey", {})
        keys = hotkeys.get("TriggerKeys", []) if isinstance(hotkeys, dict) else []
        if isinstance(keys, dict):
            return [str(keys[key]) for key in sorted(keys, key=str)]
        if isinstance(keys, (list, tuple)):
            return [str(key) for key in keys]
        return [str(keys)] if keys else []

    def _get_readonly_config(self, uri: str) -> dict:
        if not self.iface:
            self.last_status_error = "Fcitx5 is not connected."
            return {}
        try:
            values, _metadata = self._call_controller(
                "GetConfig",
                uri,
                timeout=DBUS_TIMEOUT_SECONDS,
                retry_owner_loss=True,
            )
            return self._clean_dbus(values)
        except Exception as e:
            self.last_status_error = str(e)
            return {}

    def get_fcitx_status(self):
        """Read Fcitx's current input method and active state."""
        if not self.iface:
            self.last_status_error = "Fcitx5 is not connected."
            return None
        try:
            status = {
                "current_input_method": str(
                    self._call_controller(
                        "CurrentInputMethod",
                        timeout=DBUS_TIMEOUT_SECONDS,
                        retry_owner_loss=True,
                    )
                ),
                "state": int(
                    self._call_controller(
                        "State",
                        timeout=DBUS_TIMEOUT_SECONDS,
                        retry_owner_loss=True,
                    )
                ),
            }
            self.last_status_error = ""
            return status
        except Exception as e:
            self.last_status_error = str(e)
            return None

    def set_vietnamese_active(self, active: bool) -> bool:
        """Change EVKey activation and verify Fcitx applied requested state."""
        if not self.iface:
            self.last_status_error = "Fcitx5 is not connected."
            return False
        try:
            current = str(
                self._call_controller(
                    "CurrentInputMethod",
                    timeout=DBUS_TIMEOUT_SECONDS,
                    retry_owner_loss=True,
                )
            )
            if active:
                if current != "evkey":
                    self._call_controller(
                        "SetCurrentIM",
                        "evkey",
                        timeout=DBUS_TIMEOUT_SECONDS,
                    )
                self._call_controller("Activate", timeout=DBUS_TIMEOUT_SECONDS)
            elif current == "evkey":
                self._call_controller("Deactivate", timeout=DBUS_TIMEOUT_SECONDS)

            status = self.get_fcitx_status()
            applied = status is not None and (
                status["current_input_method"] == "evkey"
                and status["state"] == 2
            ) == active
            if not applied:
                raise RuntimeError("Fcitx did not apply the requested EVKey state.")
            self.last_status_error = ""
            return True
        except Exception as e:
            self.last_status_error = str(e)
            return False

    def set_config(self, values_dict: dict) -> bool:
        """Set config and send to Fcitx5. Returns True on success, False otherwise."""
        if not self.iface:
            return False
        try:
            dbus_dict = self._prepare_dbus_data(values_dict)
            self._call_controller(
                "SetConfig",
                self.addon_name,
                dbus_dict,
                timeout=DBUS_TIMEOUT_SECONDS,
            )
            self.last_error = ""
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_sub_config_list(self, path: str, root_key: str) -> list:
        """Get sub config list from Fcitx5 and convert to Python list."""
        if not self.iface:
            return []
        try:
            full_path = f"{self.addon_name}/{path}"
            values, metadata = self._call_controller(
                "GetConfig",
                full_path,
                timeout=DBUS_TIMEOUT_SECONDS,
                retry_owner_loss=True,
            )
            self.last_error = ""
            clean_values = self._clean_dbus(values)

            array_dict = clean_values.get(root_key, {})
            if isinstance(array_dict, dict):
                sorted_keys = sorted(
                    array_dict.keys(),
                    key=lambda k: (0, int(k)) if str(k).isdigit() else (1, str(k)),
                )
                return [array_dict[k] for k in sorted_keys]
            if isinstance(array_dict, list):
                return array_dict
            return []
        except Exception as e:
            self.last_error = str(e)
            return []

    def set_sub_config_list(self, path: str, root_key: str, data_list: list) -> bool:
        """Set sub config list and send to Fcitx5. Returns True on success, False otherwise."""
        if not self.iface:
            return False
        try:
            full_path = f"{self.addon_name}/{path}"
            fcitx_array = {str(i): item for i, item in enumerate(data_list)}
            dbus_payload = {root_key: fcitx_array}
            dbus_dict = self._prepare_dbus_data(dbus_payload)
            self._call_controller(
                "SetConfig",
                full_path,
                dbus_dict,
                timeout=DBUS_TIMEOUT_SECONDS,
            )
            self.last_error = ""
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def _prepare_dbus_data(self, data):
        """Prepare data to be sent to Fcitx5 in dbus types with signatures."""
        if isinstance(data, dict):
            # Fcitx5 expects dicts to be a{sv} (String to Variant)
            formatted = {str(k): self._prepare_dbus_data(v) for k, v in data.items()}
            return dbus.Dictionary(formatted, signature="sv")
        elif isinstance(data, list):
            # Arrays must be Array of Variants (av)
            formatted = [self._prepare_dbus_data(v) for v in data]
            return dbus.Array(formatted, signature="v")
        elif isinstance(data, bool):
            return dbus.Boolean(data)
        elif isinstance(data, int):
            return dbus.Int32(data)
        elif isinstance(data, float):
            return dbus.Double(data)
        elif data is None:
            return dbus.String("")
        else:
            return dbus.String(str(data))

    def _clean_dbus(self, data):
        """Convert dbus types to Python types."""
        if isinstance(data, dbus.Dictionary):
            return {str(k): self._clean_dbus(v) for k, v in data.items()}
        elif isinstance(data, (dbus.Array, dbus.Struct, list, tuple)):
            return [self._clean_dbus(v) for v in data]
        elif isinstance(data, dbus.Boolean):
            return bool(data)
        elif isinstance(
            data,
            (dbus.Int16, dbus.Int32, dbus.Int64, dbus.UInt16, dbus.UInt32, dbus.UInt64),
        ):
            return int(data)
        elif isinstance(data, dbus.Double):
            return float(data)
        elif isinstance(data, dbus.String):
            return str(data)
        return data
