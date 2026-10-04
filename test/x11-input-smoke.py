import ctypes
import ctypes.util
import time
import sys


def _library(name):
    path = ctypes.util.find_library(name)
    if not path:
        raise RuntimeError(f"missing {name} library")
    return ctypes.CDLL(path)


x11 = _library("X11")
xtst = _library("Xtst")
Display = ctypes.c_void_p
Window = ctypes.c_ulong

x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = Display
x11.XDefaultRootWindow.argtypes = [Display]
x11.XDefaultRootWindow.restype = Window
x11.XDefaultScreen.argtypes = [Display]
x11.XDefaultScreen.restype = ctypes.c_int
x11.XQueryTree.argtypes = [
    Display,
    Window,
    ctypes.POINTER(Window),
    ctypes.POINTER(Window),
    ctypes.POINTER(ctypes.POINTER(Window)),
    ctypes.POINTER(ctypes.c_uint),
]
x11.XQueryTree.restype = ctypes.c_int
x11.XFetchName.argtypes = [Display, Window, ctypes.POINTER(ctypes.c_char_p)]
x11.XFetchName.restype = ctypes.c_int
x11.XFree.argtypes = [ctypes.c_void_p]
x11.XSetInputFocus.argtypes = [Display, Window, ctypes.c_int, ctypes.c_ulong]
x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
x11.XStringToKeysym.restype = ctypes.c_ulong
x11.XKeysymToKeycode.argtypes = [Display, ctypes.c_ulong]
x11.XKeysymToKeycode.restype = ctypes.c_uint
x11.XTranslateCoordinates.argtypes = [
    Display,
    Window,
    Window,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(Window),
]
x11.XFlush.argtypes = [Display]
x11.XSync.argtypes = [Display, ctypes.c_int]
xtst.XTestFakeMotionEvent.argtypes = [
    Display,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_ulong,
]
xtst.XTestFakeButtonEvent.argtypes = [Display, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeKeyEvent.argtypes = [Display, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]


def _children(display, window):
    root = Window()
    parent = Window()
    children = ctypes.POINTER(Window)()
    count = ctypes.c_uint()
    if not x11.XQueryTree(
        display,
        window,
        ctypes.byref(root),
        ctypes.byref(parent),
        ctypes.byref(children),
        ctypes.byref(count),
    ):
        return []
    result = [children[index] for index in range(count.value)]
    if children:
        x11.XFree(ctypes.cast(children, ctypes.c_void_p))
    return result


def _window_title(display, window):
    title = ctypes.c_char_p()
    if not x11.XFetchName(display, window, ctypes.byref(title)):
        return ""
    value = title.value.decode(errors="replace") if title.value else ""
    if title:
        x11.XFree(ctypes.cast(title, ctypes.c_void_p))
    return value


def _find_window(display, root, prefix):
    pending = [root]
    while pending:
        window = pending.pop()
        title = _window_title(display, window)
        if title.startswith(prefix):
            return window
        pending.extend(_children(display, window))
    return None


def _send_key(display, keysym_name):
    keysym = x11.XStringToKeysym(keysym_name.encode())
    keycode = x11.XKeysymToKeycode(display, keysym)
    if not keycode:
        raise RuntimeError(f"no keycode for {keysym_name}")
    xtst.XTestFakeKeyEvent(display, keycode, 1, 30)
    xtst.XTestFakeKeyEvent(display, keycode, 0, 30)
    x11.XFlush(display)
    time.sleep(0.04)


display = x11.XOpenDisplay(None)
if not display:
    raise RuntimeError("cannot open X11 display")
root = x11.XDefaultRootWindow(display)
window = _find_window(display, root, "EVKey Linux Community Settings")
if not window:
    raise RuntimeError("settings window not found on X11 display")

x11.XSetInputFocus(display, window, 2, 0)
root_x = ctypes.c_int()
root_y = ctypes.c_int()
child = Window()
if not x11.XTranslateCoordinates(
    display,
    window,
    root,
    300,
    560,
    ctypes.byref(root_x),
    ctypes.byref(root_y),
    ctypes.byref(child),
):
    raise RuntimeError("could not map input field coordinates")
xtst.XTestFakeMotionEvent(
    display,
    x11.XDefaultScreen(display),
    root_x.value,
    root_y.value,
    30,
)
xtst.XTestFakeButtonEvent(display, 1, 1, 30)
xtst.XTestFakeButtonEvent(display, 1, 0, 30)
x11.XFlush(display)
time.sleep(0.5)

ctrl = x11.XKeysymToKeycode(display, x11.XStringToKeysym(b"Control_L"))
a_code = x11.XKeysymToKeycode(display, x11.XStringToKeysym(b"a"))
xtst.XTestFakeKeyEvent(display, ctrl, 1, 30)
xtst.XTestFakeKeyEvent(display, a_code, 1, 30)
xtst.XTestFakeKeyEvent(display, a_code, 0, 30)
xtst.XTestFakeKeyEvent(display, ctrl, 0, 30)
x11.XFlush(display)
time.sleep(0.2)
_send_key(display, "BackSpace")

if "--toggle" in sys.argv:
    space = x11.XKeysymToKeycode(display, x11.XStringToKeysym(b"space"))
    xtst.XTestFakeKeyEvent(display, ctrl, 1, 30)
    xtst.XTestFakeKeyEvent(display, space, 1, 30)
    xtst.XTestFakeKeyEvent(display, space, 0, 30)
    xtst.XTestFakeKeyEvent(display, ctrl, 0, 30)
    x11.XFlush(display)
    time.sleep(0.4)

for character in "tooi ddang gox tieengs vieetj ":
    _send_key(display, "space" if character == " " else character)

time.sleep(1)
x11.XSync(display, 0)
print("Sent Telex sample through XTest to focused settings typing field")
