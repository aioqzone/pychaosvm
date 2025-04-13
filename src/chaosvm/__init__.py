from typing import List, Literal, Optional, Tuple, overload

from chaosvm.parse import parse_vm
from chaosvm.proxy.dom import TDC, Window


@overload
def prepare(
    js_vm: str,
    ip: str,
    ua="",
    href="",
    referer="",
    TDC_itoken="",
    mouse_track: Optional[List[Tuple[int, int]]] = None,
    *,
    return_window: Optional[Literal[False]] = False,
) -> TDC: ...


@overload
def prepare(
    js_vm: str,
    ip: str,
    ua="",
    href="",
    referer="",
    TDC_itoken="",
    mouse_track: Optional[List[Tuple[int, int]]] = None,
    *,
    return_window: Literal[True] = True,
) -> Window: ...


def prepare(
    js_vm: str,
    ip: str,
    ua="",
    href="",
    referer="",
    TDC_itoken="",
    mouse_track: Optional[List[Tuple[int, int]]] = None,
    *,
    return_window: Optional[bool] = False,
):
    """Create a window and get its :class:`TDC` object.

    :param js_vm: chaosvm scripts string.
    :param ip: a fake ipv4 address.
    :param ua: fake user agent, default as an internal windows UA.
    :param referer: fake referer, default as an internal referer.
    :param TDC_itoken: an optional user-preserved ``TDC_itoken``.
    :param mouse_track: __Deprecated__ . Used in slide captcha.
    :param return_window: return the window object instead of the :class:`TDC` object.

    :raise RuntimeError: if JS operation mismatched.

    :return: The window object if `return_window`, else the :class:`TDC` object of the window.
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
    if TDC_itoken:
        win.document.cookie = TDC_itoken
        win.sessionStorage.setItem("TDC_itoken", TDC_itoken)
        win.localStorage.setItem("TDC_itoken", TDC_itoken)

    if mouse_track:
        win.add_mouse_track(mouse_track)

    parse_vm(js_vm, win)(win)

    if return_window:
        return win

    return win.TDC
