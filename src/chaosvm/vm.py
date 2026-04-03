from __future__ import annotations

from ctypes import c_int32, c_uint32
from os.path import sep
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, overload

from chaosvm.opfeats import OP_NAMES
from chaosvm.proxy.dom import *

if TYPE_CHECKING:
    from .proxy.dom import Window


def signed(n: int) -> int:
    return c_int32(n).value


def unsigned(n: int) -> int:
    return c_uint32(n).value


class BuiltinOps:
    pc: int
    """program counter"""
    opcode: Tuple[int, ...]
    """operation code sequence, read-only"""
    stack: List[Any]
    """program stack"""
    call_stack: List
    """call stack"""
    window: Window
    """Global object"""

    def __init__(
        self,
        pc: int,
        opcodes: Tuple[int, ...],
        window: Window,
        opmap: Dict[int, int],
        stack: Optional[List] = None,
    ) -> None:
        self.pc = pc
        self.window = window
        self.opcode = opcodes or (0,)
        self.opmap = opmap
        self.empty_init = stack is None
        self.stack = stack or [[self.window], [{}]]
        self.call_stack = []
        self.err = None

        # fmt: off
        self.ops = [self.getattr,self.inst,self.stepout,self.geq,self.copy,self.inv,self.arr_popleft,self.grwinattr,self.zstr,self.clear,self.eq,self.vm_factory,self.assign,self.typeof,self.outcall,self.new,self.inst_arr,self.stop,self.swap,self.check_err,self.throw,self.contains,self.setattr,self.add,self.n2list,self.chobj,self.getobj,self.refeq,self.stepin,self.group,self.wincall,self.drop,self.undefined,self.jump,self.mul,self.je,self.ge,self.rshift,self.mod,self.delattr,self.false,self.get_global,self.bitor,self.sub,self.xor,self.grobj,self.new_attr,self.true,self.getobj2,self.bitand,self.urshift,self.realloc,self.tolist,self.div,self.grgetattr,self.lshift,self.null,self.concat]
        # fmt: on
        assert tuple(op.__name__ for op in self.ops) == OP_NAMES
        self.__cat_idx = self.ops.index(self.concat)
        self.__req_idx = self.ops.index(self.refeq)

    @overload
    def _curcode(self) -> int: ...

    @overload
    def _curcode(self, n: int) -> Tuple[int, ...]: ...

    def _curcode(self, n=1):
        if n == 1:
            i = self.opcode[self.pc]
        else:
            i = self.opcode[self.pc : self.pc + n]
        self.pc += n
        return i

    # =====================================================
    #                       Memory
    # =====================================================
    def inst(self):
        self.stack.append(self._curcode())

    def assign(self):
        self.stack[-1] = self._curcode()

    def undefined(self):
        self.stack.append(Undefined())

    def null(self):
        if self.opmap[self._curcode()] == self.__req_idx:
            self.stack.append(self.stack[-1] is NULL.s)
        else:
            self.pc -= 1
            self.stack.append(NULL())

    def true(self):
        self.stack.append(True)

    def false(self):
        self.stack.append(False)

    def inst_arr(self):
        self.stack.append([self._curcode()])

    def drop(self):
        self.stack.pop()

    def realloc(self):
        i = self._curcode()
        if len(self.stack) > i:
            self.stack = self.stack[:i]
        elif len(self.stack) < i:
            self.stack += [None] * (i - len(self.stack))

    # =====================================================
    #                   Call Management
    # =====================================================

    def stepin(self):
        op1, op2 = self._curcode(2)
        self.call_stack.append([op1, len(self.stack), op2])

    def jump(self):
        self.pc = self.opcode[self.pc]

    def je(self):
        i = self._curcode()
        if self.stack[-1]:
            self.pc = i

    def stepout(self):
        self.call_stack.pop()

    def outcall(self):
        nargs = self._curcode()

        if nargs:
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        obj, name = self.stack.pop()[:2]
        if obj is None or isinstance(obj, Undefined):
            raise ProxyException(
                TypeError(f"Cannot read properties of undefined (reading '{name}')")
            )
        elif isinstance(obj, Function):
            self.stack.append(getattr(obj, name)(*args))
        else:
            if isinstance(obj, str):
                obj = String(obj)
            elif isinstance(obj, (int, float)):
                obj = Number(obj)

            if (func := getattr(obj, name)) is None or isinstance(func, Undefined):
                raise ProxyException(TypeError("undefined is not a function"))

            self.stack.append(func(*args))

    def wincall(self):
        nargs = self._curcode()

        if nargs:
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        if isinstance(f := self.stack[-1], Function):
            self.stack[-1] = f.call(self.window, *args)
        else:
            self.stack[-1] = f(*args)

    def vm_factory(self):
        pc, Alen, Ulen = self._curcode(3)
        A = {}
        for _ in range(Alen):
            i, j = self._curcode(2)
            A[i] = self.stack[j]
        A = [A.get(i) for i in range(max(A) + 1)] if A else []
        U = self._curcode(Ulen)
        if isinstance(U, int):
            U = (U,)

        def vmcall(*args):
            new_stack = A.copy()
            new_stack += [None] * (max(3, 1 + max(U or [0])) - len(new_stack))
            new_stack[0] = [func.this or self.window]
            new_stack[1] = [args]
            new_stack[2] = [func]
            for i, a in zip(U, args):
                if i > 0:
                    new_stack[i] = [a]
            return ChaosVM(pc, self.opcode, self.window, self.opmap, new_stack)()

        func = Function(vmcall, self.window)
        self.stack.append(func)

    def clear(self):
        self.err = None

    def stop(self):
        return True

    def check_err(self):
        return bool(self.err)

    def throw(self):
        if isinstance(i := self.stack[-1], ProxyException):
            raise i
        raise ProxyException(self.stack[-1])

    # =====================================================
    #                        Logic
    # =====================================================
    def ge(self):
        self.stack[-1] = self.stack[-2] > self.stack.pop()

    def geq(self):
        if isinstance(self.stack[-2], String):
            self.stack[-1] = float(self.stack[-2]._s) >= self.stack.pop()
        else:
            self.stack[-1] = self.stack[-2] >= self.stack.pop()

    def inv(self):
        self.stack[-1] = not self.stack[-1]

    def eq(self):
        self.stack[-1] = self.stack[-2] == self.stack.pop()

    def refeq(self):
        if isinstance(i := self.stack.pop(), (str, int)):
            self.stack[-1] = self.stack[-1] == i  # string interning
        else:
            self.stack[-1] = self.stack[-1] is i

    def contains(self):
        self.stack[-1] = self.stack[-2] in self.stack.pop()

    # =====================================================
    #                        Arithmetical
    # =====================================================
    def add(self):
        if isinstance(i := self.stack.pop(), String):
            i = i._s
        if isinstance(i, str):
            self.stack[-1] = str(self.stack[-1]) + i
        elif isinstance(self.stack[-1], str):
            self.stack[-1] = self.stack[-1] + str(i)
        else:
            self.stack[-1] = self.stack[-1] + i

    def sub(self):
        self.stack[-1] = self.stack[-2] - self.stack.pop()

    def mul(self):
        self.stack[-1] = self.stack[-2] * self.stack.pop()

    def div(self):
        self.stack[-1] = self.stack[-2] / self.stack.pop()
        if (i := int(self.stack[-1])) == self.stack[-1]:
            self.stack[-1] = i

    def mod(self):
        self.stack[-1] = self.stack[-2] % self.stack.pop()

    def bitor(self):
        if isinstance(i := self.stack[-2], float):
            i = int(i)
        self.stack[-1] = signed(i | self.stack.pop())

    def bitand(self):
        self.stack[-1] = signed(self.stack[-2] & self.stack.pop())

    def xor(self):
        self.stack[-1] = signed(self.stack[-2] ^ self.stack.pop())

    def lshift(self):
        if self.stack[-2] != self.stack[-2]:  # NaN
            self.stack[-1] = 0 << self.stack.pop()
            return
        self.stack[-1] = signed(self.stack[-2] << self.stack.pop())

    def rshift(self):
        """(signed) right shift `>>`"""
        self.stack[-1] = signed(self.stack[-2] >> self.stack.pop())

    def urshift(self):
        """unsigned right shift `>>>`"""
        self.stack[-1] = unsigned(self.stack[-2]) >> self.stack.pop()

    # =====================================================
    #                        String
    # =====================================================

    def zstr(self):
        s = bytearray()
        while self.opmap[self._curcode()] == self.__cat_idx:
            s.append(self._curcode())
        self.pc -= 1
        self.stack.append(s.decode())

    def concat(self):
        i = self._curcode()
        self.stack[-1] += chr(i)

    # =====================================================
    #                        OOP
    # =====================================================
    def new(self):
        nargs = self._curcode()

        if nargs:
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        self.stack[-1] = self.stack[-1](*args)

    def new_attr(self):
        nargs = self._curcode()

        if nargs:
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        obj, name = self.stack[-1][:2]
        self.stack[-1] = obj[name](*args)

    def tolist(self):
        self.stack[-1] = [i for i in self.stack[-1]]

    def group(self):
        self.stack[-1] = [self.stack[-2], self.stack.pop()]

    def grgetattr(self):
        obj, name = self.stack[-2][:2]
        self.stack[-1] = [obj[name], self.stack.pop()]

    def getattr(self):
        obj, attr = self.stack.pop()[:2]
        if obj is None:
            raise ProxyException(
                TypeError(f"Cannot read properties of undefined (reading '{attr}')")
            )
        if isinstance(obj, str) and attr == "length":
            self.stack.append(len(obj))
            return
        self.stack.append(obj[attr])

    def setattr(self):
        obj, name = self.stack[-2][:2]
        obj[name] = self.stack[-1]

    def delattr(self):
        obj, name = self.stack[-1][:2]
        del obj[name]
        self.stack.append(name not in obj)

    def get_global(self):
        self.stack[-1] = self.window[self.stack[-1]]

    def grwinattr(self):
        self.stack[-1] = [self.window, self.stack[-1]]

    def typeof(self):
        self.stack[-1] = {
            type: "function",
            Symbol: "symbol",
            int: "number",
            float: "number",
            type(None): "undefined",
            str: "string",
            String: "string",
            NULL: "object",
        }[type(self.stack[-1])]

    def grobj(self):
        if isinstance((i := self.stack[-2]), list):
            assert len(i) == 1
            i = i[0]
        self.stack[-1] = [self.stack[i][0], self.stack.pop()]

    def getobj(self):
        i = self._curcode()
        if ls := self.stack[i]:
            self.stack.append(ls[0])
        else:
            self.stack.append(None)

    def getobj2(self):
        self.stack[-1] = self.stack[self.stack[-1][0]][0]

    def chobj(self):
        if ls := self.stack[self.stack[-2][0]]:
            ls[0] = self.stack[-1]
        else:
            ls.append(self.stack[-1])

    # =====================================================
    #                       Advanced
    # =====================================================

    def copy(self):
        self.stack.append(self.stack[-1])

    def swap(self):
        i = self._curcode()
        t = self.stack[-2 - i]
        self.stack[-2 - i] = self.stack[-1]
        self.stack[-1] = t

    def n2list(self):
        i = self._curcode()
        if self.stack[i] is None:
            self.stack[i] = []

    def arr_popleft(self):
        if len(self.stack[-1]):
            self.stack += [self.stack[-1].pop(0), True]
        else:
            self.stack += [None, False]


class ChaosVM(BuiltinOps):
    v = 0

    def __call__(self) -> Any:
        while True:
            try:
                E = False
                while not E:
                    i = self._curcode()
                    E = self.ops[self.opmap[i]]()
                    pass
                if self.err:
                    raise self.err

                if self.empty_init:
                    self.stack.pop()
                    return self.stack[3 + self.v :]
                else:
                    return self.stack.pop()
            except ProxyException as h:
                if not self.call_stack:
                    raise
                if f"{sep}chaosvm{sep}" in str(h.stack):
                    raise

                self.pc, stack_len, catch = self.call_stack.pop()[:3]
                self.err = h
                self.stack = self.stack[:stack_len]
                if catch:
                    if len(i := self.stack[catch]) > 0:
                        i[0] = self.err
                    else:
                        i.append(self.err)
