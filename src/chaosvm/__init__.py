from typing import List, Optional, Tuple

from chaosvm.parse import parse_vm
from chaosvm.proxy.dom import Window


def prepare(
    js_vm: str,
    ip: str,
    ua="",
    href="",
    referer="",
    mouse_track: Optional[List[Tuple[float, float]]] = None,
):
    win = Window(top=True)
    if ip:
        win.RTCPeerConnection._ip = ip
    if ua:
        win.navigator.userAgent = ua
    if href:
        win.location.href = href
    if referer:
        win.location.referer = referer
    if mouse_track:
        win.add_mouse_track(mouse_track)

    parse_vm(js_vm, win)(win)
    return win.TDC
