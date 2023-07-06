from chaosvm.parse import parse_vm
from chaosvm.proxy.dom import Window


def execute(js_vm: str):
    parse_vm(js_vm, win := Window())(win)
    return win.TDC
