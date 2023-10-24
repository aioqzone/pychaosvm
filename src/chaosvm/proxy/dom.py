from __future__ import annotations

import re
from base64 import b64encode
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Union
from urllib.parse import quote

from lxml.html import fromstring
from typing_extensions import Self

from chaosvm.proxy.builtins import Function

from . import element as ele
from .builtins import *

if TYPE_CHECKING:
    from chaosvm.stack import ChaosStack


class EventTarget:
    class MouseEvent(Proxy):
        pass

    def __init__(self) -> None:
        super().__init__()
        self.__events__ = defaultdict(list)  # type: dict[str, list[tuple[Callable, bool]]]

    def addEventListener(
        self,
        event: str,
        listener: Function,
        useCapture: bool = False,
    ):
        self.__events__[event].append((listener, useCapture))

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            if name in self.__events__:
                return self.__events__[name][0]
            raise


class Location(Proxy):
    href = "https://t.captcha.qq.com/template/drag_ele.html"
    referer = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin"


class CSSObjectModel(Proxy):
    def supports(self, prop: str, value=None):
        return True


class CSSStyleDeclaration(Proxy):
    def __init__(self, ele: ele.HtmlElement, **kw) -> None:
        super().__init__(**kw)
        self.ele = ele

    def getPropertyValue(self, prop: str):
        return "rgb(0, 255, 0)"


class Document(Proxy, EventTarget):
    documentMode = None
    characterSet = "UTF-8"
    cookie = ""
    location = Location()

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.documentElement = self.createElement("html")
        self.body = self.createElement("body")
        self.head = self.createElement("head")
        self.documentElement.appendChild(self.head)
        self.documentElement.appendChild(self.body)

    def createElement(self, tag: str, options=None) -> ele.HtmlElement:
        tag = str(tag).lower()
        if tag in (
            d := dict(
                canvas=ele.Canvas,
                iframe=ele.Iframe,
                style=ele.Style,
                video=ele.Video,
            )
        ):
            return d[tag]()
        return ele.HtmlElement(fromstring(f"<{tag}></{tag}>"))

    def getElementById(self, name: str):
        if (i := self.documentElement.e.get_element_by_id(str(name), None)) is None:
            return
        if i.tag == "video":
            return ele.Video(i)
        return ele.HtmlElement(i)

    def addEventListener(self, event: str, listener: Function, useCapture: bool = False):
        super().addEventListener(event, listener, useCapture)
        if event == "mousemove" and self._track:
            for x, y in self._track:
                listener(None, EventTarget.MouseEvent(type="mouseevent", pageX=x, pageY=y))


class ServiceWorkerContainer(Proxy):
    pass


class Navigator(Proxy):
    cookieEnabled = True
    languages = Array("zh-CN", "en", "en-GB", "en-US")
    userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64"
    platform = "Win32"
    hardwareConcurrency = 8
    appVersion = userAgent[8:]
    vendor = "Google Inc."
    appName = "Netscape"
    webdriver = False
    serviceWorker = ServiceWorkerContainer()

    class MIDIAccess(Proxy):
        pass

    # class ServiceWorkerContainer(Proxy):
    #     pass

    def requestMIDIAccess(self, MIDIOptions: Optional[Proxy] = None):
        return Promise(lambda set_result, _: set_result(self.MIDIAccess()))


class Console(Proxy):
    def log(self, *args):
        print(*args)


class RTCPeerConnection(Proxy):
    _ip = "114.5.1.4"

    class RPCDataChannel(Proxy):
        def __init__(self, label: str, options: Optional[dict] = None) -> None:
            super().__init__()
            self.label = label
            self.options = options or {}

    class RTCSessionDescription(Proxy):
        pass

    class RTCPeerConnectionIceEvent(Proxy):
        pass

    class RTCIceCandidate(Proxy):
        pass

    def __init__(self, servers: dict, *args) -> None:
        super().__init__()
        self.server = servers
        self.localDescription = self.RTCSessionDescription()

    def createDataChannel(self, label: str, options: Optional[dict] = None):
        return self.RPCDataChannel(label, options)

    def __setitem__(self, name, value):
        super().__setitem__(name, value)
        if name == "onicecandidate":
            ice = self.RTCPeerConnectionIceEvent(
                candidate=self.RTCIceCandidate(
                    candidate=f"a=candidate:735671172 1 udp 2113937151 {self._ip} 60444 typ host generation 0 network-cost 999"
                )
            )
            value(None, ice)

    def createOffer(self, options: Optional[dict] = None):
        offer = self.RTCSessionDescription(
            sdp=f"a=candidate:735671172 1 udp 2113937151 {self._ip} 60444 typ host generation 0 network-cost 999"
        )
        return Promise(lambda set_result, _: set_result(offer))

    def setLocalDescription(self, offer):
        self.localDescription = offer


class Screen(Proxy):
    availHeight = 792
    availLeft = 0
    availTop = 0
    availWidth = 1408
    colorDepth = 24
    height = 792
    isExtended = False
    pixelDepth = 24
    width = 1408


class SessionStorage(Proxy):
    def getItem(self, name: str):
        return self[name]

    def setItem(self, name: str, v):
        self[name] = str(v)


class TDC(Proxy):
    getInfo: Callable[[], Proxy]
    getData: Callable[[Optional["Window"], bool], str]
    setData: Callable[[Proxy], None]
    clearTc: Callable[[], None]


class SyncManager(Proxy):
    pass


class MediaQueryList(Proxy):
    pass


class Window(Proxy, EventTarget):
    TCaptchaReferrer = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin"
    undefined = None
    document = Document()
    navigator = Navigator()
    console = Console()
    screen = Screen()
    sessionStorage = SessionStorage()
    localStorage = SessionStorage()
    CSS = CSSObjectModel()
    SyncManager = SyncManager()

    innerWidth = 300
    innerHeight = 230

    Date = Date
    Math = Math
    JSON = JSON
    Array = Array
    Object = Object
    String = String
    Number = Number
    Symbol = Symbol
    RegExp = RegExp
    Error = JsError
    customElements = ele.CustomElementRegistry
    RTCPeerConnection = RTCPeerConnection

    TDC: TDC
    __TENCENT_CHAOS_STACK: ChaosStack
    top: Self

    def __init__(self, top=True) -> None:
        super().__init__()
        if top:
            self.__class__.top = self

    def __repr__(self):
        return "<Window>" if self.top is self else "<Window (Iframe)>"

    @property
    def window(self):
        return self

    @property
    def location(self):
        return self.document.location

    def btoa(self, s: str):
        return b64encode(s.encode()).decode()

    def setTimeout(self, cb: Callable[[], Any], ms: float):
        cb()

    def setInterval(self, func: Function, delay=0, *args):
        func(None, *args)

    def clearInterval(self, tid):
        return

    def parseInt(self, s: str, base: int):
        s = re.split(r"[^\d]", s, maxsplit=1)[0]
        return int(s, base)

    def encodeURIComponent(self, s: Union[str, String]):
        if isinstance(s, String):
            s = s._s
        return String(quote(s))

    def getComputedStyle(self, element: ele.HtmlElement, pseudoElt=None):
        return CSSStyleDeclaration(element)

    def matchMedia(self, mediaQueryString: str):
        return MediaQueryList(matches="no-preference" in mediaQueryString)

    def add_mouse_track(self, track: List[Tuple[int, int]]):
        self.document._track = track
