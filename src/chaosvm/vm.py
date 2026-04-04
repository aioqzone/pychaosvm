"""ChaosVM - Unified VM executor supporting both funarr and switch instruction sets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple

from .vm_funarr import FunarrOps
from .vm_switch import SwitchOps

if TYPE_CHECKING:
    from .proxy.dom import Window

__all__ = ["ChaosVM", "FunarrOps", "SwitchOps", "FunarrOps", "detect_vm_type_from_opcodes"]


def detect_vm_type_from_opcodes(opcodes: Tuple[int, ...]) -> str:
    """Detect VM type from opcode characteristics.

    Switch VM characteristics:
    - Maximum opcode value typically > 57 (funarr max)
    - Uses opcodes 5, 73, 83, 92 (ADD_IMM, STR_CHAR, PRE_INC, PRE_DEC)

    Returns 'switch' or 'funarr'.
    """
    assert opcodes
    max_op = max(opcodes)

    # If max opcode exceeds funarr range, likely switch
    if max_op > 68:
        return "switch"

    # Check for switch-specific opcodes
    switch_indicators = {5, 73, 83, 92}
    if any(op in opcodes for op in switch_indicators):
        return "switch"

    return "funarr"


class ChaosVM:
    """Unified VM executor.

        Automatically detects VM type (funarr or switch) and dispatches
    to the appropriate implementation.
    """

    def __init__(
        self,
        pc: int,
        opcode: Tuple[int, ...],
        window: Window,
        opmap: dict[int, int],
        stack: list[Any] | None = None,
        vm_type: str = "auto",
    ) -> None:
        """Initialize VM.

        Args:
            pc: Initial program counter
            opcode: Bytecode sequence
            window: Global window object
            opmap: Opcode to function index mapping
            stack: Optional initial stack/registers
            vm_type: 'funarr', 'switch', or 'auto' for detection
        """
        self.vm_type = detect_vm_type_from_opcodes(opcode) if vm_type == "auto" else vm_type

        if self.vm_type == "switch":
            self.impl = SwitchOps(pc, opcode, window, opmap, stack)
        else:
            self.impl = FunarrOps(pc, opcode, window, opmap, stack)

    def __call__(self) -> Any:
        """Execute the VM and return result."""
        return self.impl.execute()

    @property
    def pc(self) -> int:
        return self.impl.pc

    @property
    def stack(self) -> list[Any]:
        return self.impl.stack

    @property
    def window(self) -> Window:
        return self.impl.window
