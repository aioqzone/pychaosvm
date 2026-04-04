"""Funarr-style VM implementation (58 opcodes).

This VM uses a stack-based model with function array dispatch,
matching the structure in js/snippet/U.js.
"""

from __future__ import annotations

from os.path import sep
from typing import TYPE_CHECKING, Any, List, Tuple, overload

from chaosvm.opfeats import FUNARR_OP_FEATS, FUNARR_OP_NAMES

from .proxy.dom import NULL, Function, ProxyException, Undefined
from .vm_unified import UnifiedOps

if TYPE_CHECKING:
    from .proxy.dom import Window


class FunarrOps(UnifiedOps):
    """Funarr-style VM with 58 opcodes.

    Data model:
    - pc: Program counter
    - opcode: Bytecode array
    - stack: Program stack (LIFO)
    - call_stack: Call/exception handling stack
    - window: Global context
    """

    pc: int
    opcode: Tuple[int, ...]
    stack: List[Any]
    call_stack: List[Any]
    window: Window
    err: Any
    opmap: dict[int, int]
    empty_init: bool
    v: int = 0

    def __init__(
        self,
        pc: int,
        opcodes: Tuple[int, ...],
        window: Window,
        opmap: dict[int, int],
        stack: List[Any] | None = None,
    ) -> None:
        self.pc = pc
        self.window = window
        self.opcode = opcodes or (0,)
        self.opmap = opmap
        self.empty_init = stack is None
        self.stack = stack or [[self.window], [{}]]
        self.call_stack = []
        self.err = None

        # Verify opmap matches expected features
        self._verify_ops()

        self.__cat_idx = self.ops.index(self.__class__.concat)
        self.__req_idx = self.ops.index(self.__class__.refeq)

    def _verify_ops(self) -> None:
        """Verify that ops list matches expected operation names."""
        actual_names = tuple(op.__name__ for op in self.ops)
        if actual_names != FUNARR_OP_NAMES:
            raise RuntimeError(
                f"Ops mismatch: expected {len(FUNARR_OP_NAMES)} ops, got {len(actual_names)}"
            )

    @overload
    def _curcode(self) -> int: ...

    @overload
    def _curcode(self, n: int) -> tuple[int, ...]: ...

    def _curcode(self, n: int = 1) -> int | tuple[int, ...]:
        """Read next bytecode(s) and advance PC."""
        if n == 1:
            i = self.opcode[self.pc]
        else:
            i = self.opcode[self.pc : self.pc + n]
        self.pc += n
        return i

    # =====================================================
    #                   Memory Operations
    # =====================================================

    def immediate(self) -> None:
        """Push immediate value onto stack."""
        self.stack.append(self._curcode())

    def assign(self) -> None:
        """Assign immediate to top of stack."""
        self.stack[-1] = self._curcode()

    def undefined(self) -> None:
        """Push undefined onto stack."""
        self.stack.append(Undefined())

    def null(self) -> None:
        """Push null onto stack or check for null."""
        # Check if next opcode is refeq for null check
        if self.opmap[self._curcode()] == self.__req_idx:
            self.stack.append(self.stack[-1] is NULL.s)
        else:
            self.pc -= 1
            self.stack.append(NULL())

    def true(self) -> None:
        """Push true onto stack."""
        self.stack.append(True)

    def false(self) -> None:
        """Push false onto stack."""
        self.stack.append(False)

    def inst_arr(self) -> None:
        """Push array with single element onto stack."""
        self.stack.append([self._curcode()])

    def drop(self) -> None:
        """Pop from stack."""
        self.stack.pop()

    def realloc(self) -> None:
        """Resize stack to specified length."""
        i = self._curcode()
        if len(self.stack) > i:
            self.stack = self.stack[:i]
        elif len(self.stack) < i:
            self.stack += [None] * (i - len(self.stack))

    def copy(self) -> None:
        """Copy top of stack."""
        self.stack.append(self.stack[-1])

    def swap(self) -> None:
        """Swap stack elements."""
        i = self._curcode()
        t = self.stack[-2 - i]
        self.stack[-2 - i] = self.stack[-1]
        self.stack[-1] = t

    def n2list(self) -> None:
        """Convert stack position to list if None."""
        i = self._curcode()
        if self.stack[i] is None:
            self.stack[i] = []

    # =====================================================
    #                   Call Management
    # =====================================================

    def stepin(self) -> None:
        """Enter function call."""
        op1, op2 = self._curcode(2)
        self.call_stack.append([op1, len(self.stack), op2])

    def stepout(self) -> None:
        """Exit function call."""
        self.call_stack.pop()

    def jump(self) -> None:
        """Unconditional jump."""
        self.pc = self.opcode[self.pc]

    def je(self) -> None:
        """Jump if true."""
        i = self._curcode()
        if self.stack[-1]:
            self.pc = i

    def clear(self) -> None:
        """Clear error state."""
        self.err = None

    def stop(self) -> bool:
        """Stop execution."""
        return True

    def check_err(self) -> bool:
        """Check if error exists."""
        return bool(self.err)

    def throw(self) -> None:
        """Throw exception."""
        if isinstance(i := self.stack[-1], ProxyException):
            raise i
        raise ProxyException(self.stack[-1])

    # =====================================================
    #                   Logic Operations
    # =====================================================

    def ge(self) -> None:
        """Greater than comparison."""
        self.stack[-1] = self._gt(self.stack[-2], self.stack.pop())

    def geq(self) -> None:
        """Greater than or equal comparison."""
        from .proxy.dom import String

        if isinstance(self.stack[-2], String):
            self.stack[-1] = float(self.stack[-2]._s) >= self.stack.pop()
        else:
            self.stack[-1] = self._ge(self.stack[-2], self.stack.pop())

    def inv(self) -> None:
        """Logical NOT."""
        self.stack[-1] = self._inv(self.stack[-1])

    def eq(self) -> None:
        """Equality comparison."""
        self.stack[-1] = self._eq(self.stack[-2], self.stack.pop())

    def refeq(self) -> None:
        """Reference equality comparison."""
        self.stack[-1] = self._refeq(self.stack[-2], self.stack.pop())

    def contains(self) -> None:
        """Check if element is in container."""
        self.stack[-1] = self._contains(self.stack[-2], self.stack.pop())

    # =====================================================
    #                   Arithmetic Operations
    # =====================================================

    def add(self) -> None:
        """Add top two stack elements."""
        b = self.stack.pop()
        a = self.stack[-1]
        self.stack[-1] = self._add(a, b)

    def sub(self) -> None:
        """Subtract."""
        self.stack[-1] = self._sub(self.stack[-2], self.stack.pop())

    def mul(self) -> None:
        """Multiply."""
        self.stack[-1] = self._mul(self.stack[-2], self.stack.pop())

    def div(self) -> None:
        """Divide."""
        self.stack[-1] = self._div(self.stack[-2], self.stack.pop())

    def mod(self) -> None:
        """Modulo."""
        self.stack[-1] = self._mod(self.stack[-2], self.stack.pop())

    def bitor(self) -> None:
        """Bitwise OR."""
        self.stack[-1] = self._bitor(self.stack[-2], self.stack.pop())

    def bitand(self) -> None:
        """Bitwise AND."""
        self.stack[-1] = self._bitand(self.stack[-2], self.stack.pop())

    def xor(self) -> None:
        """Bitwise XOR."""
        self.stack[-1] = self._xor(self.stack[-2], self.stack.pop())

    def lshift(self) -> None:
        """Left shift."""
        self.stack[-1] = self._lshift(self.stack[-2], self.stack.pop())

    def rshift(self) -> None:
        """Right shift (signed)."""
        self.stack[-1] = self._rshift(self.stack[-2], self.stack.pop())

    def urshift(self) -> None:
        """Unsigned right shift."""
        self.stack[-1] = self._urshift(self.stack[-2], self.stack.pop())

    # =====================================================
    #                   String Operations
    # =====================================================

    def zstr(self) -> None:
        """Construct string. (optimized version)

        Initialize empty string if it is called w/o succeeding concat (original functionality).
        Construct a bytearray and decode it if it is called w/ succeeding concat operation.
        """
        s = bytearray()
        while self.opmap[self._curcode()] == self.__cat_idx:
            s.append(self._curcode())
        self.pc -= 1
        self.stack.append(s.decode())

    def concat(self) -> None:
        """Concatenate character to string."""
        i = self._curcode()
        self.stack[-1] = self._concat_char(self.stack[-1], i)

    # =====================================================
    #                   Object Operations
    # =====================================================

    def getattr(self) -> None:
        """Get object attribute."""
        obj, attr = self.stack.pop()[:2]
        self.stack.append(self._getattr(obj, attr))

    def setattr(self) -> None:
        """Set object attribute."""
        obj, name = self.stack[-2][:2]
        self._setattr(obj, name, self.stack[-1])

    def delattr(self) -> None:
        """Delete object attribute."""
        obj, name = self.stack[-1][:2]
        self.stack.append(self._delattr(obj, name))

    def get_global(self) -> None:
        """Get global variable."""
        self.stack[-1] = self.window[self.stack[-1]]

    def typeof(self) -> None:
        """Get type of value."""
        self.stack[-1] = self._typeof(self.stack[-1])

    def grwinattr(self) -> None:
        """Group window attribute."""
        self.stack[-1] = [self.window, self.stack[-1]]

    def grgetattr(self) -> None:
        """Group and get attribute."""
        obj, name = self.stack[-2][:2]
        self.stack[-1] = [obj[name], self.stack.pop()]

    def grobj(self) -> None:
        """Group object."""
        if isinstance((i := self.stack[-2]), list):
            assert len(i) == 1
            i = i[0]
        self.stack[-1] = [self.stack[i][0], self.stack.pop()]

    def group(self) -> None:
        """Group two stack elements."""
        self.stack[-1] = [self.stack[-2], self.stack.pop()]

    def new(self) -> None:
        """Call constructor."""
        if nargs := self._curcode():
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        self.stack[-1] = self.stack[-1](*args)

    def new_attr(self) -> None:
        """Call constructor via attribute."""
        if nargs := self._curcode():
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        obj, name = self.stack[-1][:2]
        self.stack[-1] = obj[name](*args)

    def chobj(self) -> None:
        """Change object reference."""
        if ls := self.stack[self.stack[-2][0]]:
            ls[0] = self.stack[-1]
        else:
            ls.append(self.stack[-1])

    def getobj(self) -> None:
        """Get object from stack position."""
        i = self._curcode()
        if ls := self.stack[i]:
            self.stack.append(ls[0])
        else:
            self.stack.append(None)

    def getobj2(self) -> None:
        """Get object from indexed position."""
        self.stack[-1] = self.stack[self.stack[-1][0]][0]

    def tolist(self) -> None:
        """Convert to list."""
        self.stack[-1] = [i for i in self.stack[-1]]

    def arr_popleft(self) -> None:
        """Pop left from array."""
        if len(self.stack[-1]):
            self.stack += [self.stack[-1].pop(0), True]
        else:
            self.stack += [None, False]

    # =====================================================
    #                   Call Operations
    # =====================================================

    def outcall(self) -> None:
        """Call method on object."""
        if nargs := self._curcode():
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        obj, name = self.stack.pop()[:2]
        result = self._call_method(obj, name, args)
        self.stack.append(result)

    def wincall(self) -> None:
        """Call function with window context."""
        if nargs := self._curcode():
            args = self.stack[-nargs:]
            self.stack = self.stack[:-nargs]
        else:
            args = []

        func = self.stack[-1]
        self.stack[-1] = self._call_func(func, self.window, args)

    def vm_factory(self) -> None:
        """Create VM function factory."""
        pc, alen, ulen = self._curcode(3)

        # Build argument map
        A = {}
        for _ in range(alen):
            i, j = self._curcode(2)
            A[i] = self.stack[j]

        A = [A.get(i) for i in range(max(A) + 1)] if A else []
        U = self._curcode(ulen)
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
            # Create new VM instance and execute
            vm = FunarrOps(pc, self.opcode, self.window, self.opmap, new_stack)
            return vm.execute()

        func = Function(vmcall, self.window)
        self.stack.append(func)

    # =====================================================
    #                   Execution
    # =====================================================

    def execute(self) -> Any:
        """Execute the VM until completion."""
        while True:
            try:
                E = False
                while not E:
                    i = self._curcode()
                    E = self.ops[self.opmap[i]](self)
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

    # Build operation dispatch list
    ops = (
        getattr,
        immediate,
        stepout,
        geq,
        copy,
        inv,
        arr_popleft,
        grwinattr,
        zstr,
        clear,
        eq,
        vm_factory,
        assign,
        typeof,
        outcall,
        new,
        inst_arr,
        stop,
        swap,
        check_err,
        throw,
        contains,
        setattr,
        add,
        n2list,
        chobj,
        getobj,
        refeq,
        stepin,
        group,
        wincall,
        drop,
        undefined,
        jump,
        mul,
        je,
        ge,
        rshift,
        mod,
        delattr,
        false,
        get_global,
        bitor,
        sub,
        xor,
        grobj,
        new_attr,
        true,
        getobj2,
        bitand,
        urshift,
        realloc,
        tolist,
        div,
        grgetattr,
        lshift,
        null,
        concat,
    )
