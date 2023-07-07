from chaosvm.parse import parse_vm
from chaosvm.proxy.dom import Window
from typing import List, Tuple, Optional


def prepare(js_vm: str, mouse_track: Optional[List[Tuple[float, float]]] = None):
    (win := Window()).add_mouse_track(mouse_track or [])
    parse_vm(js_vm, win)(win)
    return win.TDC
