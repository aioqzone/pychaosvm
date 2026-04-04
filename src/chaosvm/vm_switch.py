"""Switch-style VM implementation (96 opcodes).

This VM uses a register-based model with switch-case instruction dispatch,
matching the structure in js/snippet/switch.js.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

from chaosvm.opfeats import SWITCH_OP_FEATS, SWITCH_OP_NAMES

from .proxy.dom import ProxyException
from .vm_unified import UnifiedOps

if TYPE_CHECKING:
    from .proxy.dom import Window


class SwitchOps(UnifiedOps):
    """Switch-style VM with 96 opcodes.

    Data model:
    - pc: Program counter (K in JS)
    - opcode: Bytecode array (o in JS)
    - stack: Register array (R in JS) - preallocated slots
    - call_stack: Call/exception stack (C in JS)
    - err: Current exception (U in JS)
    - window: Global context (Q in JS)

    Register layout:
    - R[0]: Typically holds [window]
    - R[1]: Arguments
    - R[2]: Function reference
    - R[3+]: Local variables and temporaries
    """

    pc: int
    opcode: Tuple[int, ...]
    stack: List[Any]  # Acts as register file R
    call_stack: List[Any]
    window: Window
    err: Any

    # Temporary workspace (w in JS)
    w: List[Any]
    # Temporary counter (T in JS)
    T: int

    def __init__(
        self,
        pc: int,
        opcodes: Tuple[int, ...],
        window: Window,
        opmap: dict[int, int],
        stack: List[Any] | None = None,
    ) -> None:
        self.pc = pc
        self.opcode = opcodes
        self.window = window
        self.opmap = opmap
        self.call_stack = []
        self.err = None
        self.w = []
        self.T = 0

        # Initialize register file (preallocate 256 slots)
        if stack is not None:
            self.stack = stack
        else:
            self.stack = [None] * 256
            self.stack[0] = [window]  # R[0] = [window]

        # Verify opmap matches expected features
        self._verify_opmap()

    def _verify_opmap(self) -> None:
        """Verify that opmap matches expected instruction features."""
        for opcode_idx, func_idx in self.opmap.items():
            # This would need the actual syntax hash calculation
            # For now, just validate indices are in range
            if func_idx >= len(SWITCH_OP_NAMES):
                raise RuntimeError(f"Opmap index {func_idx} out of range")

    def _curcode(self) -> int:
        """Read next bytecode and advance PC (o[++K])."""
        i = self.opcode[self.pc]
        self.pc += 1
        return i

    def _get_reg(self, idx: int) -> Any:
        """Get register value (R[idx])."""
        return self.stack[idx]

    def _set_reg(self, idx: int, value: Any) -> None:
        """Set register value (R[idx] = value)."""
        self.stack[idx] = value

    # =====================================================
    #                   Arithmetic Operations
    # =====================================================

    def op_0_add_reg(self) -> None:
        """0: ADD_REG R[a] = R[b] + R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._add(self._get_reg(src1), self._get_reg(src2)))

    def op_5_add_imm(self) -> None:
        """5: ADD_IMM R[a] = R[b] + imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._add(self._get_reg(src), imm))

    def op_31_mul_reg(self) -> None:
        """31: MUL_REG R[a] = R[b] * R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._mul(self._get_reg(src1), self._get_reg(src2)))

    def op_54_div_reg(self) -> None:
        """54: DIV_REG R[a] = R[b] / R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._div(self._get_reg(src1), self._get_reg(src2)))

    def op_55_mod_reg(self) -> None:
        """55: MOD_REG R[a] = R[b] % R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._mod(self._get_reg(src1), self._get_reg(src2)))

    def op_61_sub_reg(self) -> None:
        """61: SUB_REG R[a] = R[b] - R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._sub(self._get_reg(src1), self._get_reg(src2)))

    def op_60_sub_imm_rev(self) -> None:
        """60: SUB_IMM_REV R[a] = imm - R[b]"""
        dst = self._curcode()
        imm = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._sub(imm, self._get_reg(src)))

    def op_79_sub_imm(self) -> None:
        """79: SUB_IMM R[a] = R[b] - imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._sub(self._get_reg(src), imm))

    def op_27_neg(self) -> None:
        """27: NEG R[a] = -R[b]"""
        dst = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._neg(self._get_reg(src)))

    def op_4_to_num_unary(self) -> None:
        """4: TO_NUM_UNARY R[a] = +R[b]"""
        dst = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._pos(self._get_reg(src)))

    def op_2_to_num(self) -> None:
        """2: TO_NUM R[a] = (bigint) ? R[b] : R[b] - 0"""
        dst = self._curcode()
        src = self._curcode()
        val = self._get_reg(src)
        self._set_reg(dst, self._to_num(val))

    # =====================================================
    #                   Bitwise Operations
    # =====================================================

    def op_8_ushr_imm(self) -> None:
        """8: USHR_IMM R[a] = R[b] >>> imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._urshift(self._get_reg(src), imm))

    def op_24_sar_imm(self) -> None:
        """24: SAR_IMM R[a] = R[b] >> imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._rshift(self._get_reg(src), imm))

    def op_32_shl_reg(self) -> None:
        """32: SHL_REG R[a] = R[b] << R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._lshift(self._get_reg(src1), self._get_reg(src2)))

    def op_71_shl_imm(self) -> None:
        """71: SHL_IMM R[a] = R[b] << imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._lshift(self._get_reg(src), imm))

    def op_72_sar_reg(self) -> None:
        """72: SAR_REG R[a] = R[b] >> R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._rshift(self._get_reg(src1), self._get_reg(src2)))

    def op_30_or_imm(self) -> None:
        """30: OR_IMM R[a] = R[b] | imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._bitor(self._get_reg(src), imm))

    def op_33_or_reg(self) -> None:
        """33: OR_REG R[a] = R[b] | R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._bitor(self._get_reg(src1), self._get_reg(src2)))

    def op_59_and_imm(self) -> None:
        """59: AND_IMM R[a] = R[b] & imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._bitand(self._get_reg(src), imm))

    def op_87_xor_reg(self) -> None:
        """87: XOR_REG R[a] = R[b] ^ R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._xor(self._get_reg(src1), self._get_reg(src2)))

    # =====================================================
    #                   Comparison Operations
    # =====================================================

    def op_6_eq_imm(self) -> None:
        """6: EQ_IMM R[a] = R[b] == imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._eq(self._get_reg(src), imm))

    def op_15_eq_reg(self) -> None:
        """15: EQ_REG R[a] = R[b] == R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._eq(self._get_reg(src1), self._get_reg(src2)))

    def op_53_seq_imm(self) -> None:
        """53: SEQ_IMM R[a] = R[b] === imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._refeq(self._get_reg(src), imm))

    def op_67_seq_reg(self) -> None:
        """67: SEQ_REG R[a] = R[b] === R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._refeq(self._get_reg(src1), self._get_reg(src2)))

    def op_14_gt_reg(self) -> None:
        """14: GT_REG R[a] = R[b] > R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._gt(self._get_reg(src1), self._get_reg(src2)))

    def op_23_lt_reg(self) -> None:
        """23: LT_REG R[a] = R[b] < R[c]"""
        dst = self._curcode()
        src1 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst, self._lt(self._get_reg(src1), self._get_reg(src2)))

    def op_45_ge_imm(self) -> None:
        """45: GE_IMM R[a] = R[b] >= imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._ge(self._get_reg(src), imm))

    def op_81_gt_imm(self) -> None:
        """81: GT_IMM R[a] = R[b] > imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._gt(self._get_reg(src), imm))

    def op_88_lt_imm(self) -> None:
        """88: LT_IMM R[a] = R[b] < imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._lt(self._get_reg(src), imm))

    def op_95_le_imm(self) -> None:
        """95: LE_IMM R[a] = R[b] <= imm"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, self._le(self._get_reg(src), imm))

    # =====================================================
    #                   Logical Operations
    # =====================================================

    def op_36_not(self) -> None:
        """36: NOT R[a] = !R[b]"""
        dst = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._inv(self._get_reg(src)))

    # =====================================================
    #                   Type Operations
    # =====================================================

    def op_22_typeof(self) -> None:
        """22: TYPEOF R[a] = typeof R[b]"""
        dst = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._typeof(self._get_reg(src)))

    # =====================================================
    #                   Constant Loading
    # =====================================================

    def op_48_load_imm(self) -> None:
        """48: LOAD_IMM R[a] = imm"""
        dst = self._curcode()
        imm = self._curcode()
        self._set_reg(dst, imm)

    def op_66_load_null(self) -> None:
        """66: LOAD_NULL R[a] = null"""
        dst = self._curcode()
        self._set_reg(dst, None)

    def op_51_load_ctx(self) -> None:
        """51: LOAD_CTX R[a] = Q (window)"""
        dst = self._curcode()
        self._set_reg(dst, self.window)

    def op_37_str_init(self) -> None:
        """37: STR_INIT R[a] = ''"""
        dst = self._curcode()
        self._set_reg(dst, "")

    def op_86_obj_new(self) -> None:
        """86: OBJ_NEW R[a] = {}"""
        dst = self._curcode()
        self._set_reg(dst, {})

    # =====================================================
    #                   String Operations
    # =====================================================

    def op_73_str_char(self) -> None:
        """73: STR_CHAR R[a] += char(imm)"""
        dst = self._curcode()
        char_code = self._curcode()
        current = self._get_reg(dst)
        self._set_reg(dst, self._concat_char(current, char_code))

    def op_21_str_char2(self) -> None:
        """21: STR_CHAR2 R[a] += char; R[b] += char"""
        dst1 = self._curcode()
        char1 = self._curcode()
        dst2 = self._curcode()
        char2 = self._curcode()
        self._set_reg(dst1, self._concat_char(self._get_reg(dst1), char1))
        self._set_reg(dst2, self._concat_char(self._get_reg(dst2), char2))

    def op_28_str_init_char(self) -> None:
        """28: STR_INIT_CHAR R[a] = ''; R[b] += char"""
        dst1 = self._curcode()
        dst2 = self._curcode()
        char = self._curcode()
        self._set_reg(dst1, "")
        self._set_reg(dst2, self._concat_char(self._get_reg(dst2), char))

    def op_64_str_char3(self) -> None:
        """64: STR_CHAR3 Three registers append char"""
        dst1 = self._curcode()
        char1 = self._curcode()
        dst2 = self._curcode()
        char2 = self._curcode()
        dst3 = self._curcode()
        char3 = self._curcode()
        self._set_reg(dst1, self._concat_char(self._get_reg(dst1), char1))
        self._set_reg(dst2, self._concat_char(self._get_reg(dst2), char2))
        self._set_reg(dst3, self._concat_char(self._get_reg(dst3), char3))

    # =====================================================
    #                   Object Property Operations
    # =====================================================

    def op_7_getprop_imm(self) -> None:
        """7: GETPROP_IMM R[a] = R[b][imm]"""
        dst = self._curcode()
        src = self._curcode()
        imm = self._curcode()
        obj = self._get_reg(src)
        self._set_reg(dst, self._getattr(obj, imm))

    def op_91_getprop_dyn(self) -> None:
        """91: GETPROP_DYN R[a] = R[b][R[c]]"""
        dst = self._curcode()
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        obj = self._get_reg(obj_reg)
        attr = self._get_reg(attr_reg)
        self._set_reg(dst, self._getattr(obj, attr))

    def op_11_setprop_ret(self) -> None:
        """11: SETPROP_RET R[a][b] = R[c]; return R[d]"""
        obj_reg = self._curcode()
        attr = self._curcode()
        val_reg = self._curcode()
        ret_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), attr, self._get_reg(val_reg))
        # Return handled by execution loop

    def op_18_getprop2(self) -> None:
        """18: GETPROP2 Two consecutive property gets"""
        dst1 = self._curcode()
        src1 = self._curcode()
        imm1 = self._curcode()
        dst2 = self._curcode()
        src2 = self._curcode()
        imm2 = self._curcode()
        self._set_reg(dst1, self._getattr(self._get_reg(src1), imm1))
        self._set_reg(dst2, self._getattr(self._get_reg(src2), imm2))

    def op_34_getprop_idx(self) -> None:
        """34: GETPROP_IDX R[a] = R[b][R[c]]; R[d] = imm"""
        dst1 = self._curcode()
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        dst2 = self._curcode()
        imm = self._curcode()
        obj = self._get_reg(obj_reg)
        attr = self._get_reg(attr_reg)
        self._set_reg(dst1, self._getattr(obj, attr))
        self._set_reg(dst2, imm)

    def op_69_setprop_imm(self) -> None:
        """69: SETPROP_IMM R[a][imm] = R[b]"""
        obj_reg = self._curcode()
        imm = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), imm, self._get_reg(val_reg))

    def op_84_setprop_dyn(self) -> None:
        """84: SETPROP_DYN R[a][R[b]] = R[c]"""
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), self._get_reg(attr_reg), self._get_reg(val_reg))

    def op_74_delprop(self) -> None:
        """74: DELPROP R[a] = delete R[b][R[c]]"""
        dst = self._curcode()
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        result = self._delattr(self._get_reg(obj_reg), self._get_reg(attr_reg))
        self._set_reg(dst, result)

    def op_35_in(self) -> None:
        """35: IN R[a] = R[b] in R[c]"""
        dst = self._curcode()
        attr_reg = self._curcode()
        obj_reg = self._curcode()
        self._set_reg(dst, self._contains(self._get_reg(attr_reg), self._get_reg(obj_reg)))

    # =====================================================
    #                   Array Operations
    # =====================================================

    def op_40_array_iter(self) -> None:
        """40: ARRAY_ITER w = R[a]; if (w.length) R[b] = w.shift(); else ++K"""
        w_reg = self._curcode()
        dst = self._curcode()
        self.w = self._get_reg(w_reg)
        if self.w and len(self.w) > 0:
            self._set_reg(dst, self.w.pop(0))
            # Success case - continue to next (read condition register)
            cond_reg = self._curcode()
            self._set_reg(cond_reg, True)
        else:
            # Empty - skip next instruction
            cond_reg = self._curcode()
            self._set_reg(cond_reg, False)
            self.pc += 1  # Skip the instruction that would use the value

    def op_85_array_new(self) -> None:
        """85: ARRAY_NEW R[a] = Array(imm)"""
        dst = self._curcode()
        size = self._curcode()
        self._set_reg(dst, [None] * size)

    # =====================================================
    #                   Control Flow
    # =====================================================

    def op_1_jcond(self) -> None:
        """1: JCOND K += R[a] ? imm1 : imm2"""
        cond_reg = self._curcode()
        offset_true = self._curcode()
        offset_false = self._curcode()
        if self._get_reg(cond_reg):
            self.pc += offset_true
        else:
            self.pc += offset_false

    def op_76_jmp(self) -> None:
        """76: JMP K += imm"""
        offset = self._curcode()
        self.pc += offset

    def op_17_ret(self) -> None:
        """17: RET return R[a]"""
        # Return from current function - this will be handled by the execution loop
        pass

    def op_93_ret_ctx(self) -> None:
        """93: RET_CTX R[a] = Q; return R[b]"""
        ctx_reg = self._curcode()
        self._set_reg(ctx_reg, self.window)
        # Return handled by execution loop

    def op_83_pre_inc(self) -> None:
        """83: PRE_INC R[a] = ++R[b]"""
        dst = self._curcode()
        src = self._curcode()
        val = self._get_reg(src)
        new_val = val + 1
        self._set_reg(src, new_val)
        self._set_reg(dst, new_val)

    def op_92_pre_dec(self) -> None:
        """92: PRE_DEC R[a] = --R[b]"""
        dst = self._curcode()
        src = self._curcode()
        val = self._get_reg(src)
        new_val = val - 1
        self._set_reg(src, new_val)
        self._set_reg(dst, new_val)

    # =====================================================
    #                   Exception Handling
    # =====================================================

    def op_10_throw(self) -> None:
        """10: THROW throw R[a]"""
        src = self._curcode()
        from .proxy.dom import ProxyException

        raise ProxyException(self._get_reg(src))

    def op_19_catch_setup(self) -> None:
        """19: CATCH_SETUP R[a] = U; R[b] = R[c]; C.push(K + imm)"""
        exc_reg = self._curcode()
        copy_reg = self._curcode()
        offset = self._curcode()
        self._set_reg(exc_reg, self.err)
        self._set_reg(copy_reg, self._get_reg(copy_reg))
        self.call_stack.append(self.pc + offset)

    def op_25_push_catch(self) -> None:
        """25: PUSH_CATCH R[a] = R[b]; C.push(K + imm)"""
        dst = self._curcode()
        src = self._curcode()
        offset = self._curcode()
        self._set_reg(dst, self._get_reg(src))
        self.call_stack.append(self.pc + offset)

    def op_29_pop_catch(self) -> None:
        """29: POP_CATCH C.pop()"""
        if self.call_stack:
            self.call_stack.pop()

    def op_46_load_exc(self) -> None:
        """46: LOAD_EXC R[a] = U"""
        dst = self._curcode()
        self._set_reg(dst, self.err)

    # =====================================================
    #                   Call Operations
    # =====================================================

    def op_12_call_0(self) -> None:
        """12: CALL_0 R[a] = R[b].call(Q)"""
        dst = self._curcode()
        func_reg = self._curcode()
        func = self._get_reg(func_reg)
        result = self._call_func(func, self.window, [])
        self._set_reg(dst, result)

    def op_39_call_1(self) -> None:
        """39: CALL_1 R[a] = R[b].call(R[c])"""
        dst = self._curcode()
        func_reg = self._curcode()
        this_reg = self._curcode()
        func = self._get_reg(func_reg)
        this_val = self._get_reg(this_reg)
        result = self._call_func(func, this_val, [])
        self._set_reg(dst, result)

    def op_65_call_1_ctx(self) -> None:
        """65: CALL_1_CTX R[a] = R[b].call(Q, R[c])"""
        dst = self._curcode()
        func_reg = self._curcode()
        arg1_reg = self._curcode()
        func = self._get_reg(func_reg)
        arg1 = self._get_reg(arg1_reg)
        result = self._call_func(func, self.window, [arg1])
        self._set_reg(dst, result)

    def op_78_call_2(self) -> None:
        """78: CALL_2 R[a] = R[b].call(R[c], R[d], R[e])"""
        dst = self._curcode()
        func_reg = self._curcode()
        this_reg = self._curcode()
        arg1_reg = self._curcode()
        arg2_reg = self._curcode()
        func = self._get_reg(func_reg)
        this_val = self._get_reg(this_reg)
        result = self._call_func(
            func, this_val, [self._get_reg(arg1_reg), self._get_reg(arg2_reg)]
        )
        self._set_reg(dst, result)

    def op_94_call_2_ctx(self) -> None:
        """94: CALL_2_CTX R[a] = R[b].call(Q, R[c], R[d])"""
        dst = self._curcode()
        func_reg = self._curcode()
        arg1_reg = self._curcode()
        arg2_reg = self._curcode()
        func = self._get_reg(func_reg)
        result = self._call_func(
            func, self.window, [self._get_reg(arg1_reg), self._get_reg(arg2_reg)]
        )
        self._set_reg(dst, result)

    def op_20_call_3(self) -> None:
        """20: CALL_3 R[a] = R[b].call(R[c], R[d], R[e], R[f])"""
        dst = self._curcode()
        func_reg = self._curcode()
        this_reg = self._curcode()
        args = [self._get_reg(self._curcode()) for _ in range(3)]
        func = self._get_reg(func_reg)
        this_val = self._get_reg(this_reg)
        result = self._call_func(func, this_val, args)
        self._set_reg(dst, result)

    def op_63_call_3_ctx(self) -> None:
        """63: CALL_3_CTX R[a] = R[b].call(Q, R[c], R[d], R[e])"""
        dst = self._curcode()
        func_reg = self._curcode()
        args = [self._get_reg(self._curcode()) for _ in range(3)]
        func = self._get_reg(func_reg)
        result = self._call_func(func, self.window, args)
        self._set_reg(dst, result)

    def op_68_apply(self) -> None:
        """68: APPLY R[a] = R[b].apply(R[c], w)"""
        dst = self._curcode()
        func_reg = self._curcode()
        this_reg = self._curcode()
        func = self._get_reg(func_reg)
        this_val = self._get_reg(this_reg)
        result = self._call_func(func, this_val, self.w)
        self._set_reg(dst, result)

    # =====================================================
    #                   Constructor Operations
    # =====================================================

    def op_9_new_1(self) -> None:
        """9: NEW_1 R[a] = new R[b](R[c])"""
        dst = self._curcode()
        ctor_reg = self._curcode()
        arg_reg = self._curcode()
        ctor = self._get_reg(ctor_reg)
        arg = self._get_reg(arg_reg)
        self._set_reg(dst, ctor(arg))

    def op_62_new_0(self) -> None:
        """62: NEW_0 R[a] = new R[b]()"""
        dst = self._curcode()
        ctor_reg = self._curcode()
        ctor = self._get_reg(ctor_reg)
        self._set_reg(dst, ctor())

    def op_89_new_2(self) -> None:
        """89: NEW_2 R[a] = new R[b](R[c], R[d])"""
        dst = self._curcode()
        ctor_reg = self._curcode()
        arg1_reg = self._curcode()
        arg2_reg = self._curcode()
        ctor = self._get_reg(ctor_reg)
        self._set_reg(dst, ctor(self._get_reg(arg1_reg), self._get_reg(arg2_reg)))

    # =====================================================
    #                   Copy Operations
    # =====================================================

    def op_26_mov(self) -> None:
        """26: MOV R[a] = R[b]"""
        dst = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._get_reg(src))

    def op_58_dup2(self) -> None:
        """58: DUP2 R[a] = R[b]; R[c] = R[d]"""
        dst1 = self._curcode()
        src1 = self._curcode()
        dst2 = self._curcode()
        src2 = self._curcode()
        self._set_reg(dst1, self._get_reg(src1))
        self._set_reg(dst2, self._get_reg(src2))

    # =====================================================
    #                   Keys/Iterator Operations
    # =====================================================

    def op_56_keys(self) -> None:
        """56: KEYS w = []; for (T in R[a]) w.push(T); R[b] = w"""
        src_reg = self._curcode()
        dst_reg = self._curcode()
        obj = self._get_reg(src_reg)
        self.w = []
        if isinstance(obj, dict):
            for key in obj.keys():
                self.w.append(key)
        self._set_reg(dst_reg, self.w)

    # =====================================================
    #                   Complex Operations (PLACEHOLDER)
    # =====================================================

    def op_3_push_ret(self) -> None:
        """3: PUSH_RET C.push(K + imm) - Function call setup"""
        offset = self._curcode()
        self.call_stack.append(self.pc + offset)

    def op_13_getprop_call(self) -> None:
        """13: GETPROP_CALL Get property and call method"""
        # Complex composite - split into atomic operations
        # R[a] = R[b][R[c]]
        self.op_91_getprop_dyn()
        # Then call operation
        dst = self._curcode()
        func_reg = self._curcode()
        this_reg = self._curcode()
        func = self._get_reg(func_reg)
        this_val = self._get_reg(this_reg)
        result = self._call_func(func, this_val, [])
        self._set_reg(dst, result)

    def op_16_setprop2(self) -> None:
        """16: SETPROP2 R[a] = R[b]; R[c][R[d]] = R[e]"""
        dst = self._curcode()
        src = self._curcode()
        self._set_reg(dst, self._get_reg(src))
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), self._get_reg(attr_reg), self._get_reg(val_reg))

    def op_38_setprop2_ctx(self) -> None:
        """38: SETPROP2_CTX Set two properties and load context"""
        # First property set
        obj1 = self._curcode()
        attr1 = self._curcode()
        val1 = self._curcode()
        self._setattr(self._get_reg(obj1), self._get_reg(attr1), self._get_reg(val1))
        # Second property set
        obj2 = self._curcode()
        attr2 = self._curcode()
        val2 = self._curcode()
        self._setattr(self._get_reg(obj2), self._get_reg(attr2), self._get_reg(val2))
        # Load context
        dst = self._curcode()
        self._set_reg(dst, self.window)

    def op_41_call_1_save(self) -> None:
        """41: CALL_1_SAVE Call and save additional register"""
        # Call with context
        dst = self._curcode()
        func_reg = self._curcode()
        arg_reg = self._curcode()
        save_dst = self._curcode()
        save_src = self._curcode()
        func = self._get_reg(func_reg)
        arg = self._get_reg(arg_reg)
        result = self._call_func(func, self.window, [arg])
        self._set_reg(dst, result)
        self._set_reg(save_dst, self._get_reg(save_src))

    def op_42_str_char_set(self) -> None:
        """42: STR_CHAR_SET String append + property set"""
        # String append
        str_reg = self._curcode()
        char = self._curcode()
        self._set_reg(str_reg, self._concat_char(self._get_reg(str_reg), char))
        # Property set
        obj_reg = self._curcode()
        attr = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), attr, self._get_reg(val_reg))

    def op_43_str_char_set_clr(self) -> None:
        """43: STR_CHAR_SET_CLR Append, set, and clear"""
        # String append
        str_reg = self._curcode()
        char = self._curcode()
        self._set_reg(str_reg, self._concat_char(self._get_reg(str_reg), char))
        # Property set
        obj_reg = self._curcode()
        attr = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), attr, self._get_reg(val_reg))
        # Clear
        clear_reg = self._curcode()
        self._set_reg(clear_reg, "")

    def op_44_str_char_obj(self) -> None:
        """44: STR_CHAR_OBJ Append, create object, clear"""
        # String append
        str_reg = self._curcode()
        char = self._curcode()
        self._set_reg(str_reg, self._concat_char(self._get_reg(str_reg), char))
        # Create object
        obj_reg = self._curcode()
        self._set_reg(obj_reg, {})
        # Clear
        clear_reg = self._curcode()
        self._set_reg(clear_reg, "")

    def op_47_str_char_prop(self) -> None:
        """47: STR_CHAR_PROP Append and get property"""
        # String append
        str_reg = self._curcode()
        char = self._curcode()
        self._set_reg(str_reg, self._concat_char(self._get_reg(str_reg), char))
        # Property get
        dst = self._curcode()
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        self._set_reg(dst, self._getattr(self._get_reg(obj_reg), self._get_reg(attr_reg)))

    def op_49_inc_copy(self) -> None:
        """49: INC_COPY Complex increment and copy"""
        # Convert to number
        dst1 = self._curcode()
        src1 = self._curcode()
        self._set_reg(dst1, self._to_num(self._get_reg(src1)))
        # Increment
        dst2 = self._curcode()
        src2 = self._curcode()
        val = self._get_reg(src2)
        self._set_reg(dst2, val + 1)
        # Copy
        dst3 = self._curcode()
        src3 = self._curcode()
        self._set_reg(dst3, self._get_reg(src3))

    def op_50_setprop_ret_ctx(self) -> None:
        """50: SETPROP_RET_CTX Set, load context, return"""
        # Set property
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), self._get_reg(attr_reg), self._get_reg(val_reg))
        # Load context
        ctx_reg = self._curcode()
        self._set_reg(ctx_reg, self.window)
        # Return
        # Handled by execution loop

    def op_52_str_char_prop2(self) -> None:
        """52: STR_CHAR_PROP Append and property access"""
        # String append
        str_reg = self._curcode()
        char = self._curcode()
        self._set_reg(str_reg, self._concat_char(self._get_reg(str_reg), char))
        # Property access
        dst = self._curcode()
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        self._set_reg(dst, self._getattr(self._get_reg(obj_reg), self._get_reg(attr_reg)))

    def op_57_func_create(self) -> None:
        """57: FUNC_CREATE Create function"""
        # Collect parameters
        argc = self._curcode()
        for _ in range(argc):
            self.w.append(self._get_reg(self._curcode()))
        # Create function
        dst = self._curcode()
        pc_offset = self._curcode()
        # TODO: Create actual function object
        self._set_reg(dst, lambda: None)
        # Length property
        length = self._curcode()
        # Object.defineProperty would go here

    def op_70_str_func_prop(self) -> None:
        """70: STR_FUNC_PROP String + function + property"""
        # String append
        str_reg = self._curcode()
        char = self._curcode()
        self._set_reg(str_reg, self._concat_char(self._get_reg(str_reg), char))
        # Create function
        argc = self._curcode()
        for _ in range(argc):
            self.w.append(self._get_reg(self._curcode()))
        dst = self._curcode()
        pc_offset = self._curcode()
        # Set property
        obj_reg = self._curcode()
        attr_reg = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), self._get_reg(attr_reg), self._get_reg(val_reg))

    def op_75_func_create2(self) -> None:
        """75: FUNC_CREATE2 Complex function creation"""
        # Create first function
        argc = self._curcode()
        for _ in range(argc):
            self.w.append(self._get_reg(self._curcode()))
        dst = self._curcode()
        pc_offset = self._curcode()
        length = self._curcode()
        # Set property
        obj_reg = self._curcode()
        attr = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), attr, self._get_reg(val_reg))
        # Create second function
        self.w = []
        argc2 = self._curcode()
        for _ in range(argc2):
            self.w.append(self._get_reg(self._curcode()))
        dst2 = self._curcode()
        pc_offset2 = self._curcode()
        length2 = self._curcode()

    def op_77_func_method(self) -> None:
        """77: FUNC_METHOD Create function and set as method"""
        # Set property first
        obj_reg = self._curcode()
        attr = self._curcode()
        val_reg = self._curcode()
        self._setattr(self._get_reg(obj_reg), attr, self._get_reg(val_reg))
        # Then create function
        argc = self._curcode()
        for _ in range(argc):
            self.w.append(self._get_reg(self._curcode()))
        dst = self._curcode()
        pc_offset = self._curcode()
        length = self._curcode()
        # Set as method
        obj2 = self._curcode()
        attr2 = self._curcode()
        val2 = self._curcode()
        self._setattr(self._get_reg(obj2), self._get_reg(attr2), self._get_reg(val2))

    def op_80_load_call(self) -> None:
        """80: LOAD_CALL Load immediate and call"""
        # Load immediate
        dst1 = self._curcode()
        imm = self._curcode()
        self._set_reg(dst1, imm)
        # Call
        dst2 = self._curcode()
        func_reg = self._curcode()
        arg_reg = self._curcode()
        func = self._get_reg(func_reg)
        arg = self._get_reg(arg_reg)
        result = self._call_func(func, self.window, [arg])
        self._set_reg(dst2, result)
        # Copy
        dst3 = self._curcode()
        src3 = self._curcode()
        self._set_reg(dst3, self._get_reg(src3))

    def op_82_call_2_dyn(self) -> None:
        """82: CALL_2_DYN Two argument dynamic call"""
        dst = self._curcode()
        func_reg = self._curcode()
        this_reg = self._curcode()
        arg_reg = self._curcode()
        func = self._get_reg(func_reg)
        this_val = self._get_reg(this_reg)
        arg = self._get_reg(arg_reg)
        result = self._call_func(func, this_val, [arg])
        self._set_reg(dst, result)

    def op_90_setprop_get(self) -> None:
        """90: SETPROP_GET Set property then get another"""
        # Set property
        obj1 = self._curcode()
        attr1 = self._curcode()
        val1 = self._curcode()
        self._setattr(self._get_reg(obj1), self._get_reg(attr1), self._get_reg(val1))
        # Get property
        dst2 = self._curcode()
        obj2 = self._curcode()
        attr2 = self._curcode()
        self._set_reg(dst2, self._getattr(self._get_reg(obj2), self._get_reg(attr2)))
        # Load immediate
        dst3 = self._curcode()
        imm = self._curcode()
        self._set_reg(dst3, imm)

    # =====================================================
    #                   Execution
    # =====================================================

    def execute(self) -> Any:
        """Execute the VM until completion."""
        # Build opcode dispatch table
        ops = [getattr(self, fname) for fname in SWITCH_OP_NAMES]

        while True:
            try:
                while True:
                    opcode = self._curcode()
                    mapped = self.opmap.get(opcode, opcode)
                    if mapped < len(ops) and ops[mapped]:
                        ops[mapped]()
                    else:
                        raise RuntimeError(f"Unknown opcode: {opcode} -> {mapped}")

            except ProxyException:
                if not self.call_stack:
                    raise
                # Exception handling
                self.pc = self.call_stack.pop()
                continue

            # Normal exit
            break

        # Return value handling
        return self.stack[0]  # Placeholder
