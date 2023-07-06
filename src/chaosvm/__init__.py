from __future__ import annotations
from .parse import parse_vm
from typing import TYPE_CHECKING
from .stack import ChaosStack
from pyjsparser import parse

if TYPE_CHECKING:
    from chaosvm.proxy.dom import Window


def run_vm(vm_js: str, window: Window):
    parse_vm(vm_js, window)
    stack: ChaosStack = window.__TENCENT_CHAOS_STACK
    stack.run(window)
    return window
