#!/usr/bin/env python3
"""Give the dashboard's window the mouse back.

    ./clickable.py [window class]          (default: conky-dashboard)

conky 1.25 gives an undecorated window an empty input area, so the panel is
click-through: clicks on the update rows and the buttons land on the desktop
underneath. This resets the area to the whole window. lua/dashboard.lua runs it
once when the panel starts, so there is nothing to do by hand; it waits up to
ten seconds for the window to appear.
"""

import ctypes
import sys
import time

SHAPE_INPUT, SHAPE_SET = 2, 0


class ClassHint(ctypes.Structure):
    _fields_ = [("res_name", ctypes.c_void_p), ("res_class", ctypes.c_void_p)]


def main():
    wanted = (sys.argv[1] if len(sys.argv) > 1 else "conky-dashboard").encode()
    x = ctypes.CDLL("libX11.so.6")
    shape = ctypes.CDLL("libXext.so.6")
    x.XOpenDisplay.restype = ctypes.c_void_p
    x.XDefaultRootWindow.restype = ctypes.c_ulong
    x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + [ctypes.c_void_p] * 4
    x.XGetClassHint.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ClassHint)]
    x.XFree.argtypes = [ctypes.c_void_p]
    x.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    shape.XShapeCombineMask.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
                                        ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_int]

    display = x.XOpenDisplay(None)
    if not display:
        sys.exit("clickable.py: no X display")
    # A window that closes while the tree is walked would otherwise end the
    # program through Xlib's default error handler.
    handler = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(lambda d, e: 0)
    x.XSetErrorHandler(handler)

    def windows(parent):
        root, up = ctypes.c_ulong(), ctypes.c_ulong()
        children, count = ctypes.POINTER(ctypes.c_ulong)(), ctypes.c_uint()
        if not x.XQueryTree(display, parent, ctypes.byref(root), ctypes.byref(up),
                            ctypes.byref(children), ctypes.byref(count)):
            return
        found = [children[i] for i in range(count.value)]
        if children:
            x.XFree(ctypes.cast(children, ctypes.c_void_p))
        for window in found:
            yield window
            yield from windows(window)

    def matches(window):
        hint = ClassHint()
        if not x.XGetClassHint(display, window, ctypes.byref(hint)):
            return False
        names = [ctypes.string_at(p) for p in (hint.res_name, hint.res_class) if p]
        for p in (hint.res_name, hint.res_class):
            if p:
                x.XFree(p)
        return wanted in names

    for _ in range(20):
        hits = [w for w in windows(x.XDefaultRootWindow(display)) if matches(w)]
        if hits:
            for window in hits:
                # No mask: the input area goes back to the window's own shape.
                shape.XShapeCombineMask(display, window, SHAPE_INPUT, 0, 0, 0, SHAPE_SET)
            x.XSync(display, 0)
            return
        time.sleep(0.5)
    sys.exit("clickable.py: no %s window found" % wanted.decode())


if __name__ == "__main__":
    main()
