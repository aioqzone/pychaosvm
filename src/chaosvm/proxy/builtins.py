import logging
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from json import JSONEncoder, dumps
from math import floor
from random import random
from typing import Any, Callable, ClassVar, Dict, Optional, Union

from typing_extensions import Self

log = logging.getLogger(__name__)


__all__ = [
    "NULL",
    "Proxy",
    "Object",
    "String",
    "RegExp",
    "Array",
    "Symbol",
    "Promise",
    "Date",
    "Function",
    "Number",
    "Math",
    "JSON",
    "JsError",
    "ProxyException",
]


class NULL:
    s: Self

    def __new__(cls):
        if not hasattr(cls, "s"):
            cls.s = super().__new__(cls)
        return cls.s

    def __getattribute__(self, o):
        try:
            return super().__getattribute__(str(o))
        except AttributeError:
            raise TypeError(f"Cannot read properties of null (reading '{o}')")

    def __getitem__(self, o):
        return self.__getattribute__(o)

    def __bool__(self):
        return False

    def __repr__(self) -> str:
        return "null"


class Proxy:
    def __init__(self, **kw) -> None:
        super().__init__()
        for k, v in kw.items():
            self[k] = v

    def __getattribute__(self, name: Union[str, float]):
        if isinstance(name, (int, float)):
            name = str(name)
        if name is Symbol.iterator:
            name = "__iter__"
        try:
            return super().__getattribute__(name)
        except AttributeError:
            log.debug("%s.%s not defined", self.__class__.__name__, name)
            return None

    def __setattr__(self, name: Union[str, float], __value) -> None:
        if isinstance(name, (int, float)):
            name = str(name)
        return super().__setattr__(name, __value)

    def __contains__(self, name: Union[str, float]):
        if isinstance(name, (int, float)):
            name = str(name)
        return self[name] is not None

    def __class_getitem__(cls, __name: str):
        return getattr(cls, __name)

    def __delattr__(self, name: Union[str, float]) -> None:
        if isinstance(name, (int, float)):
            name = str(name)
        return super().__delattr__(name)

    def __copy__(self):
        return self.__class__(**self.__dict__)

    def __deepcopy__(self):
        return self.__class__(**deepcopy(self.__dict__))

    __getitem__ = __getattribute__
    __setitem__ = __setattr__
    __delitem__ = __delattr__

    def __repr__(self) -> str:
        if self.__class__ is Proxy:
            return repr(self.__dict__)
        return f"<{self.__class__.__name__} {self.__dict__}>"

    @classmethod
    def defineProperty(cls, o: Self, name: str, descriptor: Union[dict, Self]):
        setattr(o, name, descriptor["get"])

    @classmethod
    def getOwnPropertyDescriptor(cls, o: Self, name: str):
        return


class Object(Proxy):
    pass


class Date(Proxy):
    TZ = timezone(timedelta(hours=8))

    def __init__(self, v: Union[int, str, None] = None) -> None:
        super().__init__()
        if isinstance(v, int):
            self.d = datetime.fromtimestamp(v / 1000, self.TZ)
        elif isinstance(v, str):
            self.d = datetime.fromisoformat(v)
        else:
            self.d = datetime.now(self.TZ)

    def getTime(self):
        return int(self.d.timestamp() * 1000)

    def getTimezoneOffset(self):
        if offset := self.d.utcoffset():
            return -int(offset.total_seconds() / 60)
        return 0


class Number(Proxy):
    def __init__(self, i) -> None:
        self._i = float(i)

    def __repr__(self) -> str:
        return repr(self._i)

    def toFixed(self, digits: int) -> str:
        fmt = f"%.{digits}f"
        return fmt % self._i


class Math(Proxy):
    @classmethod
    def random(cls):
        return random()

    @classmethod
    def floor(cls, i: float):
        return int(floor(i))


class JSON(Proxy):
    class JSJsonEncoder(JSONEncoder):
        def default(self, o: Any) -> Any:
            if isinstance(o, String):
                return o._s
            if isinstance(o, Array):
                return [o[i] for i in range(o.length)]
            if isinstance(o, Proxy):
                return o.__dict__
            if o is NULL.s:
                return None
            return super().default(o)

    @classmethod
    def stringify(cls, o):
        return String(dumps(o, cls=cls.JSJsonEncoder))


class Symbol(Proxy):
    register: ClassVar[Dict[str, Self]] = {}
    iterator: ClassVar[Self]

    def __init__(self, tag: Optional[str] = None) -> None:
        super().__init__()
        self.tag = tag

    def __getattribute__(self, __name):
        if __name == "for":
            return self.__for__
        return super().__getattribute__(__name)

    def __repr__(self) -> str:
        return f"Symbol({self.tag or ''})"

    def __for__(self, key: str):
        if key not in Symbol.register:
            Symbol.register[key] = Symbol(key)
        return Symbol.register[key]

    @classmethod
    def keyfor(cls, o: Self):
        for k, v in cls.register:
            if v is o:
                return k


Symbol.iterator = Symbol("Symbol.iterator")


class Function(Proxy):
    def __init__(self, func: Callable) -> None:
        super().__init__()
        self.__f__ = func

    def __call__(self, *args):
        return self.__f__(*args)

    def call(self, this, *args):
        return self.__f__(*args)

    def apply(self, this, args: tuple):
        return self.__f__(*args)

    def __repr__(self) -> str:
        return f"ƒ {self.__f__.__name__}"


class Promise(Proxy):
    def __init__(self, cb: Callable[[Callable[[Any], None], Callable[[str], None]], Any]) -> None:
        super().__init__()
        self.result = None
        self.exc = None
        try:
            cb(
                lambda result: setattr(self, "result", result),
                lambda exc: setattr(self, "exc", exc),
            )
        except BaseException as e:
            self.exc = e

    def then(
        self,
        resolve: Optional[Union[Function, Callable]] = None,
        reject: Optional[Callable[[BaseException], Any]] = None,
    ):
        if e := self.exc:
            if reject:
                p = Promise(lambda set_result, _: set_result(reject(e)))
                if isinstance(p.result, Promise):
                    return p.result
                return p
            return self

        if resolve:
            if isinstance(vmcall := resolve, Function):
                resolve = lambda r: vmcall(None, r)
            p = Promise(lambda set_result, _: set_result(resolve(self.result)))
            if isinstance(p.result, Promise):
                return p.result
            return p

        return self


class Array(Proxy):
    def __init__(self, *args):
        for i, k in enumerate(args):
            self[i] = k

    def __len__(self):
        return self.length

    def forEach(self, pred: Callable):
        for i in range(self.length):
            pred(None, self[i])

    @property
    def length(self):
        keys = [int(i) for i in self.__dict__ if i.isdigit()]
        return max(keys) + 1 if keys else 0

    @length.setter
    def length(self, v: int):
        keys = [int(i) for i in self.__dict__ if i.isdigit()]
        for i in filter(lambda i: i >= v, keys):
            del self[i]
        for i in range(v):
            if i not in keys:
                self[i] = None

    def __repr__(self) -> str:
        if self.length:
            return repr([self[i] for i in range(self.length)])
        return "[]"

    def indexOf(self, i):
        for k, v in self.__dict__.items():
            if v == i:
                return int(k)
        return -1

    def push(self, o):
        self[self.length] = o
        return self.length

    def unshift(self, *ele):
        n = len(ele)
        for i in range(self.length - 1, -1, -1):
            self[i + n] = self[i]
        for i, e in enumerate(ele):
            self[i] = e

    def join(self, sep=","):
        return sep.join(str(self[i]) for i in range(self.length))

    def slice(self, start: int = 0, end: Optional[int] = None):
        if end is None:
            end = self.length
        if start < 0:
            start = self.length + start
        return Array(*(self[i] for i in range(start, end)))

    def reverse(self):
        o = [self[i] for i in range(self.length)]
        for i, k in enumerate(reversed(o)):
            self[i] = k
        return self


class String(Proxy):
    _s: str

    def __init__(self, s: str) -> None:
        super().__init__(_s=str(s))

    def __repr__(self) -> str:
        return repr(self._s)

    def __str__(self):
        return self._s

    def __len__(self):
        return len(self._s)

    def split(self, sep: Union[str, "RegExp"]):
        if isinstance(sep, str):
            return Array(*self._s.split(sep))
        return Array(*sep.pattern.split(self._s))

    def indexOf(self, sub: Union[str, Self]):
        if isinstance(sub, String):
            sub = sub._s
        return self._s.find(sub)

    def match(self, reg: "RegExp"):
        if reg.G:
            return Array(*reg.pattern.findall(self._s))
        return reg.exec(self._s)

    def replace(self, reg: Union[str, Self, "RegExp"], newstr: Union[str, Function]):
        if isinstance(reg, String):
            reg = reg._s
        pattern = reg.pattern if isinstance(reg, RegExp) else re.compile(reg)
        if isinstance(newstr, str):
            return pattern.sub(newstr, self._s)
        return pattern.sub(lambda m: newstr(None, m.group()), self._s)

    def slice(self, start: int, stop: Optional[int] = None):
        return self._s[slice(start, stop)]

    def toLowerCase(self):
        return self._s.lower()

    def toUpperCase(self):
        return self._s.upper()

    def substr(self, start: int, length: Optional[int] = None):
        return self._s[start:][:length]

    def charCodeAt(self, i: int):
        return ord(self._s[i]) if i < len(self._s) else float("nan")

    @classmethod
    def fromCharCode(cls, *num: int):
        return "".join(chr(i) for i in num)

    @property
    def length(self):
        return len(self._s)


class JsError(RuntimeError):
    pass


class ProxyException(Proxy, RuntimeError):
    err: BaseException

    def __init__(self, err: BaseException, stack: str) -> None:
        super().__init__(err=err, stack=stack)

    @property
    def message(self):
        return self.err.args[0]

    def toString(self):
        return f"Error: {self.message}"


class RegExp(Proxy):
    def __init__(self, pattern: str, modifiers: str = "") -> None:
        super().__init__()
        if "g" in modifiers:
            self.G = True
            modifiers = modifiers.replace("g", "")
        else:
            self.G = False

        flags = 0
        for c in modifiers:
            flags |= dict(i=re.I, m=re.M)[c]

        self.pattern = re.compile(pattern, flags)

    def exec(self, s: str) -> Union[Array, object]:
        if m := self.pattern.search(s):
            return Array(m.group(0), *m.groups())
        return NULL()

    def test(self, s: Union[str, String]):
        if isinstance(s, String):
            s = s._s
        return self.pattern.match(s) is not None
