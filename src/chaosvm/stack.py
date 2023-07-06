from __future__ import annotations

from .vm import ChaosVM
from typing import Sequence, Dict, TYPE_CHECKING


if TYPE_CHECKING:
    from .proxy.dom import Window


class ChaosStack:
    """A ``TENCENT_CHAOS_STACK``. If is associated with an operation-code mapping,
    and can be called if given a data stack.
    """

    pc_start = 0
    """where the pc is set when vm is started."""

    def __init__(self, opmap: Dict[int, int], opcode: Sequence[int], pc=0) -> None:
        self.opmap = opmap.copy()
        self.opcode = tuple(opcode)
        """stack data in bytes"""
        self.pc_start = pc

    def __call__(self, window: Window):
        return ChaosVM(self.pc_start, self.opcode, window, self.opmap)()
