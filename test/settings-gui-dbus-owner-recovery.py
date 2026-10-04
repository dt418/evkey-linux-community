import os
import subprocess
import sys
import time

import dbus
import dbus.bus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from core.dbus_handler import FCITX_SERVICE, LotusDBusHandler

IBUS_SERVICE = "org.freedesktop.IBus"


def _serve_fcitx_mock():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(FCITX_SERVICE, bus=bus)

    class Controller(dbus.service.Object):
        @dbus.service.method(
            "org.fcitx.Fcitx.Controller1",
            in_signature="s",
            out_signature="a{sv}av",
        )
        def GetConfig(self, _uri):
            return dbus.Dictionary({}, signature="sv"), dbus.Array([], signature="v")

    Controller(bus, "/controller")
    GLib.MainLoop().run()


def _owner(bus, name):
    try:
        return bus.get_name_owner(name)
    except dbus.DBusException:
        return None


def _wait_for_owner(bus, name, expected, process=None):
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError("mock Fcitx service exited")
        owner = _owner(bus, name)
        if (process is not None and owner is not None) or (
            process is None and owner == expected
        ):
            return
        time.sleep(0.02)
    raise RuntimeError("timed out waiting for mock service owner")


def _start_fcitx_mock(bus):
    process = subprocess.Popen(
        [sys.executable, __file__, "--serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )
    _wait_for_owner(bus, FCITX_SERVICE, None, process)
    return process


def main():
    bus = dbus.SessionBus()
    ibus_name = dbus.service.BusName(
        IBUS_SERVICE,
        bus=bus,
        allow_replacement=False,
        replace_existing=False,
        do_not_queue=True,
    )
    ibus_owner = bus.get_name_owner(IBUS_SERVICE)
    first = _start_fcitx_mock(bus)
    second = None
    try:
        first_owner = bus.get_name_owner(FCITX_SERVICE)
        handler = LotusDBusHandler()
        if handler.get_config() != {"values": {}, "metadata": []}:
            raise RuntimeError("initial mock Fcitx read failed")

        first.terminate()
        first.wait(timeout=5)
        _wait_for_owner(bus, FCITX_SERVICE, None)

        # Model the handler's disconnected/backoff state without calling an
        # activatable service name while no mock owner exists.
        handler.iface = None
        handler._auto_retry_at = time.monotonic() + 30.0
        second = _start_fcitx_mock(bus)
        second_owner = bus.get_name_owner(FCITX_SERVICE)
        if second_owner == first_owner:
            raise RuntimeError("Fcitx mock owner did not change")
        if handler.get_config() != {"values": {}, "metadata": []}:
            raise RuntimeError("handler did not reconnect to returning owner")
        if bus.get_name_owner(IBUS_SERVICE) != ibus_owner:
            raise RuntimeError("IBus mock owner changed during Fcitx recovery")
        print("PASS: Fcitx owner restart recovered during backoff; IBus name coexisted")
    finally:
        for process in (first, second):
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        del ibus_name


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--serve":
        _serve_fcitx_mock()
    else:
        main()
