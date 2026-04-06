"""Tests for switch-style VM implementation."""

import pytest

from chaosvm.opfeats import (
    FUNARR_OP_COUNT,
    FUNARR_OP_NAMES,
    SWITCH_OP_COUNT,
    SWITCH_OP_NAMES,
)
from chaosvm.proxy.dom import Window
from chaosvm.vm import ChaosVM, detect_vm_type_from_opcodes
from chaosvm.vm_funarr import FunarrOps
from chaosvm.vm_switch import SwitchOps
from chaosvm.vm_unified import UnifiedOps


class TestOpfeats:
    """Test opfeats.py generation."""

    def test_funarr_op_count(self):
        assert FUNARR_OP_COUNT == 58
        assert len(FUNARR_OP_NAMES) == 58

    def test_switch_op_count(self):
        assert SWITCH_OP_COUNT == 96
        assert len(SWITCH_OP_NAMES) == 96

    def test_funarr_op_names(self):
        assert FUNARR_OP_NAMES[0] == "getattr"
        assert FUNARR_OP_NAMES[-1] == "concat"

    def test_switch_op_names(self):
        assert SWITCH_OP_NAMES[0] == "op_0_add_reg"
        assert SWITCH_OP_NAMES[95] == "op_95_le_imm"


class TestUnifiedOps:
    """Test UnifiedOps shared operations."""

    def test_arithmetic_ops(self):
        ops = UnifiedOps()

        # Add
        assert ops._add(1, 2) == 3
        assert ops._add("a", "b") == "ab"
        assert ops._add(1, "b") == "1b"

        # Sub
        assert ops._sub(5, 3) == 2

        # Mul
        assert ops._mul(3, 4) == 12

        # Div
        assert ops._div(6, 2) == 3
        assert ops._div(7, 2) == 3.5

        # Mod
        assert ops._mod(7, 3) == 1

    def test_bitwise_ops(self):
        ops = UnifiedOps()

        # OR
        assert ops._bitor(1, 2) == 3

        # AND
        assert ops._bitand(3, 1) == 1

        # XOR
        assert ops._xor(3, 1) == 2

        # Shifts
        assert ops._lshift(1, 2) == 4
        assert ops._rshift(4, 2) == 1
        assert ops._urshift(-4, 2) > 0  # Unsigned shift

    def test_comparison_ops(self):
        ops = UnifiedOps()

        # Equality
        assert ops._eq(1, 1) is True
        assert ops._eq(1, 2) is False

        # Reference equality
        assert ops._refeq(1, 1) is True
        assert ops._refeq("a", "a") is True

        # Ordering
        assert ops._gt(5, 3) is True
        assert ops._lt(3, 5) is True
        assert ops._ge(5, 5) is True
        assert ops._le(3, 3) is True


class TestVMDetection:
    """Test VM type detection."""

    def test_detect_funarr(self):
        # Funarr opcodes are typically 0-57
        opcodes = (0, 1, 2, 57)
        assert detect_vm_type_from_opcodes(opcodes) == "funarr"

    def test_detect_switch_by_max_opcode(self):
        # Switch opcodes can go up to 95
        opcodes = (0, 50, 80, 95)
        assert detect_vm_type_from_opcodes(opcodes) == "switch"

    def test_detect_switch_by_indicators(self):
        # Opcode 73 (STR_CHAR) is switch-specific
        opcodes = (0, 73, 10)
        assert detect_vm_type_from_opcodes(opcodes) == "switch"

    def test_detect_empty(self):
        with pytest.raises(ValueError):
            detect_vm_type_from_opcodes(())


class TestSwitchOpsBasic:
    """Basic tests for SwitchOps."""

    def test_init(self):
        window = Window()
        opmap = {i: i for i in range(96)}
        opcodes = tuple(range(96))

        vm = SwitchOps(0, opcodes, window, opmap)

        assert vm.pc == 0
        assert vm.window is window
        assert len(vm.stack) == 256
        assert vm.stack[0] == [window]

    def test_register_access(self):
        window = Window()
        opmap = {i: i for i in range(96)}
        vm = SwitchOps(0, (0,), window, opmap)

        # Set and get register
        vm._set_reg(5, "test_value")
        assert vm._get_reg(5) == "test_value"

        # Default is None
        assert vm._get_reg(10) is None

    def test_curcode(self):
        window = Window()
        opmap = {i: i for i in range(96)}
        opcodes = (10, 20, 30)
        vm = SwitchOps(-1, opcodes, window, opmap)  # pc=-1 to match JS semantics (o[++K])

        assert vm._curcode() == 10
        assert vm._curcode() == 20
        assert vm._curcode() == 30
        assert vm.pc == 2  # After 3 increments from -1: 2


class TestChaosVM:
    """Tests for unified ChaosVM."""

    def test_init_auto_detect_funarr(self):
        window = Window()
        opmap = {i: i for i in range(58)}
        opcodes = tuple(range(58))  # 0-57 is funarr range

        vm = ChaosVM(0, opcodes, window, opmap, vm_type="auto")

        assert vm.vm_type == "funarr"
        assert isinstance(vm.impl, FunarrOps)

    def test_init_auto_detect_switch(self):
        window = Window()
        opmap = {i: i for i in range(96)}
        opcodes = (0, 5, 73, 95)  # Contains switch-specific opcodes

        vm = ChaosVM(0, opcodes, window, opmap, vm_type="auto")

        assert vm.vm_type == "switch"
        assert isinstance(vm.impl, SwitchOps)

    def test_init_explicit_type(self):
        window = Window()
        opmap = {i: i for i in range(96)}
        opcodes = (0, 5, 73, 95)

        # Force funarr even with switch opcodes
        vm = ChaosVM(0, opcodes, window, opmap, vm_type="funarr")
        assert vm.vm_type == "funarr"


class TestSwitchInstructions:
    """Tests for individual switch instructions."""

    @pytest.fixture
    def vm(self):
        window = Window()
        opmap = {i: i for i in range(96)}
        return SwitchOps(-1, (0,) * 100, window, opmap)  # pc=-1 to match JS semantics (o[++K])

    def test_op_0_add_reg(self, vm):
        # Setup: R[1] = 5, R[2] = 3
        vm._set_reg(1, 5)
        vm._set_reg(2, 3)
        # Opcode: dst=3, src1=1, src2=2
        vm.opcode = (3, 1, 2)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_0_add_reg()

        assert vm._get_reg(3) == 8

    def test_op_5_add_imm(self, vm):
        # Setup: R[1] = 5
        vm._set_reg(1, 5)
        # Opcode: dst=2, src=1, imm=10
        vm.opcode = (2, 1, 10)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_5_add_imm()

        assert vm._get_reg(2) == 15

    def test_op_15_eq_reg(self, vm):
        # Setup: R[1] = 5, R[2] = 5
        vm._set_reg(1, 5)
        vm._set_reg(2, 5)
        # Opcode: dst=3, src1=1, src2=2
        vm.opcode = (3, 1, 2)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_15_eq_reg()

        assert vm._get_reg(3) is True

    def test_op_36_not(self, vm):
        # Setup: R[1] = True
        vm._set_reg(1, True)
        # Opcode: dst=2, src=1
        vm.opcode = (2, 1)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_36_not()

        assert vm._get_reg(2) is False

    def test_op_48_load_imm(self, vm):
        # Opcode: dst=5, imm=42
        vm.opcode = (5, 42)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_48_load_imm()

        assert vm._get_reg(5) == 42

    def test_op_66_load_null(self, vm):
        # Opcode: dst=10
        vm.opcode = (10,)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_66_load_null()

        assert vm._get_reg(10) is None

    def test_op_37_str_init(self, vm):
        # Opcode: dst=5
        vm.opcode = (5,)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_37_str_init()

        assert vm._get_reg(5) == ""

    def test_op_73_str_char(self, vm):
        # Setup: R[5] = "He"
        vm._set_reg(5, "He")
        # Opcode: dst=5, char_code=108 (l)
        vm.opcode = (5, 108)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_73_str_char()

        assert vm._get_reg(5) == "Hel"

    def test_op_83_pre_inc(self, vm):
        # Setup: R[5] = 10
        vm._set_reg(5, 10)
        # Opcode: dst=6, src=5
        vm.opcode = (6, 5)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_83_pre_inc()

        assert vm._get_reg(5) == 11  # incremented
        assert vm._get_reg(6) == 11  # result

    def test_op_92_pre_dec(self, vm):
        # Setup: R[5] = 10
        vm._set_reg(5, 10)
        # Opcode: dst=6, src=5
        vm.opcode = (6, 5)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_92_pre_dec()

        assert vm._get_reg(5) == 9  # decremented
        assert vm._get_reg(6) == 9  # result

    def test_op_26_mov(self, vm):
        # Setup: R[5] = "value"
        vm._set_reg(5, "value")
        # Opcode: dst=10, src=5
        vm.opcode = (10, 5)
        vm.pc = -1  # Match JS semantics (o[++K])

        vm.op_26_mov()

        assert vm._get_reg(10) == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
