"""Unified operations shared between Funarr and Switch VM implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .proxy.dom import NULL, Function, Number, ProxyException, String, Symbol, Undefined

if TYPE_CHECKING:
    from .proxy.dom import Window


class UnifiedOps:
    """Shared low-level operations for both Funarr and Switch VMs.

    This class provides common implementations for:
    - Arithmetic operations (add, sub, mul, div, mod)
    - Bitwise operations (or, and, xor, shifts)
    - Comparison operations (eq, refeq, gt, lt, ge, le)
    - Object operations (getattr, setattr, delattr)
    - String operations
    """

    window: Window

    # =====================================================
    #                   Arithmetic Operations
    # =====================================================

    def _add(self, a: Any, b: Any) -> Any:
        """Add two values with JavaScript semantics.

        String concatenation takes priority if either operand is a string.
        """
        # Handle String wrapper objects
        if hasattr(a, "_s"):
            a = a._s
        if hasattr(b, "_s"):
            b = b._s

        if isinstance(a, str) or isinstance(b, str):
            return str(a) + str(b)
        return a + b

    def _sub(self, a: Any, b: Any) -> Any:
        """Subtract b from a."""
        return a - b

    def _mul(self, a: Any, b: Any) -> Any:
        """Multiply a by b."""
        return a * b

    def _div(self, a: Any, b: Any) -> Any:
        """Divide a by b, returning int if result is whole number."""
        result = a / b
        if (i := int(result)) == result:
            return i
        return result

    def _mod(self, a: Any, b: Any) -> Any:
        """Modulo operation."""
        return a % b

    def _neg(self, a: Any) -> Any:
        """Unary negation."""
        return -a

    def _pos(self, a: Any) -> Any:
        """Unary plus (convert to number)."""
        return +a

    def _to_num(self, a: Any) -> Any:
        """Convert to number, preserving bigint."""
        if isinstance(a, int) and abs(a) > 2**53:
            return a
        return float(a) if a is not None else 0

    # =====================================================
    #                   Bitwise Operations
    # =====================================================

    def _signed(self, n: int) -> int:
        """Convert to signed 32-bit integer."""
        from ctypes import c_int32

        return c_int32(n).value

    def _unsigned(self, n: int) -> int:
        """Convert to unsigned 32-bit integer."""
        from ctypes import c_uint32

        return c_uint32(n).value

    def _bitor(self, a: Any, b: Any) -> int:
        """Bitwise OR."""
        if isinstance(a, float):
            a = int(a)
        return self._signed(int(a) | int(b))

    def _bitand(self, a: Any, b: Any) -> int:
        """Bitwise AND."""
        return self._signed(int(a) & int(b))

    def _xor(self, a: Any, b: Any) -> int:
        """Bitwise XOR."""
        return self._signed(int(a) ^ int(b))

    def _lshift(self, a: Any, b: Any) -> int:
        """Left shift."""
        if a != a:  # NaN check
            return 0 << int(b)
        return self._signed(int(a) << int(b))

    def _rshift(self, a: Any, b: Any) -> int:
        """Arithmetic (signed) right shift."""
        return self._signed(int(a) >> int(b))

    def _urshift(self, a: Any, b: Any) -> int:
        """Unsigned right shift."""
        return self._unsigned(int(a)) >> int(b)

    # =====================================================
    #                   Comparison Operations
    # =====================================================

    def _eq(self, a: Any, b: Any) -> bool:
        """Loose equality (==)."""
        return a == b

    def _refeq(self, a: Any, b: Any) -> bool:
        """Reference equality (===).

        For strings and integers, uses value equality.
        For other types, uses identity (is).
        """
        if isinstance(b, (str, int)):
            return a == b
        return a is b

    def _gt(self, a: Any, b: Any) -> bool:
        """Greater than."""
        return a > b

    def _lt(self, a: Any, b: Any) -> bool:
        """Less than."""
        return a < b

    def _ge(self, a: Any, b: Any) -> bool:
        """Greater than or equal."""
        return a >= b

    def _le(self, a: Any, b: Any) -> bool:
        """Less than or equal."""
        return a <= b

    def _inv(self, a: Any) -> bool:
        """Logical NOT."""
        return not a

    # =====================================================
    #                   Object Operations
    # =====================================================

    def _getattr(self, obj: Any, attr: Any) -> Any:
        """Get object attribute/property."""
        if obj is None:
            raise ProxyException(
                TypeError(f"Cannot read properties of undefined (reading '{attr}')")
            )

        # Handle string length special case
        if isinstance(obj, str) and attr == "length":
            return len(obj)

        return obj[attr]

    def _setattr(self, obj: Any, attr: Any, value: Any) -> None:
        """Set object attribute/property."""
        obj[attr] = value

    def _delattr(self, obj: Any, attr: Any) -> bool:
        """Delete object attribute, return True if successful."""
        del obj[attr]
        return attr not in obj

    def _contains(self, a: Any, b: Any) -> bool:
        """Check if a in b."""
        return a in b

    def _typeof(self, a: Any) -> str:
        """JavaScript typeof operator."""

        return {
            type: "function",
            Symbol: "symbol",
            int: "number",
            float: "number",
            type(None): "undefined",
            str: "string",
            String: "string",
            NULL: "object",
        }.get(type(a), "object")

    # =====================================================
    #                   String Operations
    # =====================================================

    def _concat_char(self, s: Any, char_code: int) -> str:
        """Append a character (by code) to string."""
        if not isinstance(s, str):
            s = ""
        return s + chr(char_code)

    def _concat_str(self, a: Any, b: Any) -> str:
        """Concatenate two strings."""
        return str(a) + str(b)

    # =====================================================
    #                   Call Operations
    # =====================================================

    def _call_method(self, obj: Any, name: str, args: list) -> Any:
        """Call a method on an object."""

        if obj is None or isinstance(obj, Undefined):
            raise ProxyException(
                TypeError(f"Cannot read properties of undefined (reading '{name}')")
            )

        if isinstance(obj, Function):
            return getattr(obj, name)(*args)

        # Wrap primitives
        if isinstance(obj, str):
            obj = String(obj)
        elif isinstance(obj, (int, float)):
            obj = Number(obj)

        func = getattr(obj, name, None)
        if func is None or isinstance(func, Undefined):
            raise ProxyException(TypeError("undefined is not a function"))

        return func(*args)

    def _call_func(self, func: Any, this: Any, args: list) -> Any:
        """Call a function with explicit this binding."""
        if isinstance(func, Function):
            return func.call(this, *args)
        return func(*args)
