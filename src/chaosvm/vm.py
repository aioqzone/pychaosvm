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

    :param opcodes: Tuple of opcode values to analyze
    :return: Detected VM type - 'switch' or 'funarr'
    :raises ValueError: if opcodes tuple is empty
    """
    if not opcodes:
        raise ValueError("opcodes is empty")

    max_op = max(opcodes)

    # If max opcode exceeds funarr range, likely switch
    if max_op > 68:
        return "switch"

    return "funarr"


class ChaosVM:
    """Unified VM executor with automatic type detection.

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

        :param pc: Initial program counter position
        :param opcode: Bytecode sequence to execute
        :param window: Global window object for execution context
        :param opmap: Mapping from opcode values to function indices
        :param stack: Optional initial stack/registers (defaults to None)
        :param vm_type: VM implementation type - 'funarr', 'switch', or 'auto' for auto-detection (defaults to 'auto')
        """
        self.vm_type = detect_vm_type_from_opcodes(opcode) if vm_type == "auto" else vm_type

        if self.vm_type == "switch":
            self.impl = SwitchOps(pc, opcode, window, opmap, stack)
        else:
            self.impl = FunarrOps(pc, opcode, window, opmap, stack)

    def __call__(self) -> Any:
        """Execute the VM and return result.

        :return: Result from VM execution
        """
        return self.impl.execute()

    @property
    def pc(self) -> int:
        """Get the current program counter position.

        :return: Current program counter value
        """
        return self.impl.pc

    @property
    def stack(self) -> list[Any]:
        """Get the current VM stack.

        :return: Current execution stack
        """
        return self.impl.stack

    @property
    def window(self) -> Window:
        """Get the global window object.

        :return: Global window execution context
        """
        return self.impl.window
