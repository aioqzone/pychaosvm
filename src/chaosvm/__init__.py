from typing import List, Optional, Tuple

from chaosvm.parse import parse_vm
from chaosvm.proxy.dom import Window


def prepare(
    js_vm: str,
    ip: str,
    ua="",
    href="",
    referer="",
    mouse_track: Optional[List[Tuple[int, int]]] = None,
):
    """Create a window and get its :class:`TDC` object.

    :param js_vm: chaosvm scripts string.
    :param ip: fake ipv4 address, default as an internal fake ip.
    :param ua: fake user agent, default as an internal windows UA.
    :param referer: fake referer, default as an internal referer.
    :param mouse_track: __Deprecated__ . Used in slide captcha.

    :return: a :class:`TDC` object.
    """
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
