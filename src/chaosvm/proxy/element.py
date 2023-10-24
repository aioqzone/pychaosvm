from __future__ import annotations

from collections import defaultdict
from copy import copy, deepcopy
from typing import Optional, Union

from lxml.html import HtmlElement as element
from lxml.html import fragment_fromstring, fragments_fromstring, tostring

from .builtins import NULL, Array, Proxy


class HtmlElement(Proxy):
    e: element
    style: CSSStyleDeclaration

    def __init__(self, ele: element, **kw) -> None:
        super().__init__(children=[], **kw)
        super().__setattr__("e", ele)
        super().__setattr__("style", CSSStyleDeclaration())

    @property
    def tag(self):
        return self.e.tag

    def __getattribute__(self, name: str | float):
        if (r := super().__getattribute__(name)) is None:
            return self.e.attrib.get(str(name)) or self.style[name]
        return r

    def __setattr__(self, name: str | float, v):
        self.e.attrib[str(name)] = str(v)
        return v

    def __delattr__(self, name: str | float):
        name = str(name)
        v = self.e.attrib[name]
        del self.e.attrib[name]
        return v

    def __contains__(self, name: str | float):
        return name in self.e.attrib or name in self.style

    def appendChild(self, o: Union[element, HtmlElement, str]):
        if isinstance(o, str):
            if i := next(self.e.iterchildren(reversed=True), None):
                i.tail = o
                return
            self.e.text = o
            return

        if isinstance(o, HtmlElement):
            o = o.e
        self.e.append(o)

    def remove(self):
        self.e.drop_tree()

    def removeChild(self, o: HtmlElement):
        self.e.remove(o.e)

    def cloneNode(self, deep=False):
        return self.__class__((deepcopy if deep else copy)(self.e), style=copy(self.style))

    def insertBefore(self, node: HtmlElement, ref: Union[HtmlElement, NULL]):
        if ref is NULL.s:
            return self.appendChild(node)
        self.e.insert(self.e.index(ref.e), node.e)
        return node

    def replaceChild(self, new: HtmlElement, old: HtmlElement):
        self.e.replace(old.e, new.e)
        return old

    def setAttribute(self, name: str, value):
        self.e.attrib[name] = str(value)

    def removeAttribute(self, name: str):
        del self.e.attrib[name]

    def getBoundingClientRect(self):
        x, y, w, h = [self.style[k] for k in ["left", "top", "width", "height"]]
        x, y, w, h = [int(k[:2]) if k else 0 for k in [x, y, w, h]]
        return DOMRect(x=x, left=x, y=y, top=y, width=w, height=h, right=x + w, bottom=y + h)

    @property
    def offsetLeft(self):
        if i := self.style.left:
            return int(i[:2])
        return 0

    @property
    def innerHTML(self) -> str:
        s = bytearray(self.e.text.encode()) if self.e.text else bytearray()
        for i in self.e.iterchildren():
            s += tostring(i)
        return s.decode()

    @innerHTML.setter
    def innerHTML(self, s: str):
        for i in self.e.iterchildren():
            self.e.remove(i)
        for i in fragments_fromstring(s):
            self.appendChild(i)

    @property
    def outerHTML(self) -> str:
        return tostring(self.e).decode()


class DOMRect(Proxy):
    pass


class CSSStyleDeclaration(Proxy):
    pass


class Video(HtmlElement):
    def __init__(self, ele: Optional[element] = None, **kw) -> None:
        if ele is None:
            ele = fragment_fromstring(
                '<video id="preview" width="160" height="120" autoplay muted></video>'
            )
        super().__init__(ele, **kw)

    class CanvasCaptureMediaStream(Proxy):
        pass

    def captureStream(self, frameRate: int = 0):
        return self.CanvasCaptureMediaStream()


class CSSStyleSheet(Proxy):
    cssRules = Array()


class Style(HtmlElement):
    sheet = CSSStyleSheet()

    def __init__(self, ele: Optional[element] = None, **kw) -> None:
        if ele is None:
            ele = fragment_fromstring("<style></style>")
        super().__init__(ele, **kw)


class Iframe(HtmlElement):
    def __init__(self, ele: Optional[element] = None, **kw) -> None:
        if ele is None:
            ele = fragment_fromstring("<iframe></iframe>")
        super().__init__(ele, **kw)

    @property
    def contentWindow(self):
        from .dom import Window

        return Window(top=False)


class Canvas(HtmlElement):
    def __init__(self, ele: Optional[element] = None, **kw) -> None:
        if ele is None:
            ele = fragment_fromstring("<canvas></canvas>")
        super().__init__(ele, **kw)

    class RenderingContext(Proxy):
        pass

    class RenderingContext2D(RenderingContext):
        def fillRect(self, x, y, w, h):
            pass

        def fillText(self, text, x, y, maxWidth=None):
            pass

    class WebGLRenderingContext(RenderingContext):
        class WebGLExtension(Proxy):
            UNMASKED_VENDOR_WEBGL = 37445
            UNMASKED_RENDERER_WEBGL = 37446

        def getSupportedExtensions(self):
            # fmt: off
            return Array('ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float', 'EXT_disjoint_timer_query', 'EXT_float_blend', 'EXT_frag_depth', 'EXT_shader_texture_lod', 'EXT_texture_compression_bptc', 'EXT_texture_compression_rgtc', 'EXT_texture_filter_anisotropic', 'EXT_sRGB', 'KHR_parallel_shader_compile', 'OES_element_index_uint', 'OES_fbo_render_mipmap', 'OES_standard_derivatives', 'OES_texture_float', 'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear', 'OES_vertex_array_object', 'WEBGL_color_buffer_float', 'WEBGL_compressed_texture_s3tc', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_renderer_info', 'WEBGL_debug_shaders', 'WEBGL_depth_texture', 'WEBGL_draw_buffers', 'WEBGL_lose_context', 'WEBGL_multi_draw')
            # fmt: on

        def getExtension(self, name: str):
            return dict(WEBGL_debug_renderer_info=self.WebGLExtension()).get(name, NULL.s)

        def getParameter(self, name: int) -> Union[str, NULL]:
            return defaultdict(
                lambda: NULL(),
                {
                    self.WebGLExtension.UNMASKED_VENDOR_WEBGL: "Google Inc. (Intel)",
                    self.WebGLExtension.UNMASKED_RENDERER_WEBGL: "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
                },
            )[name]

    class WebGL2RenderingContext(WebGLRenderingContext):
        pass

    def getContext(self, contextType: str, contextAttributes=None) -> RenderingContext:
        return {"2d": self.RenderingContext2D, "webgl": self.WebGLRenderingContext}[contextType]()

    def toDataURL(self):
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XSAAAAAXNSR0IArs4c6QAACwNJREFUeF7tm1vIdescxccOpewoFNokREJOIccUKZFyjAuHnVPsdqSQc5JTFCUhIewdFyK5EVLI2Q3ChVPO3EgkXCga9Tztp9lcX997qPWOPX7r5vv2+8415xy/seZv/Z85v32FeEEAAhAIIXBFyHlymudL4H/nu7uYvfF5j6lq/0QpMLzAU54+wjolON52XAII67j8j3V0hHUs8hz3TAQQ1pnwxb4ZYcVW133iCKuzf4TV2Xt8aoQVX+GpAiCsU2HjTccmsCesD0p6yTixX0l6jqQ7SHqcpLdL+qykd0r63Dmc/KvGPt4t6U5j3w8eP3vaOR3jHE7zwu/Cnfn10p0zNeN3bZgirAtfKSe4R2ArrEMf/KcOYe1dEJdL1kJ6n6SXSfr9eNMU1oclvV/SByR953J3yHZ6mKTrJH3lgLD8+7dIer6kOy5//10pO1YU4cWvBfrDfY2kayX9XdI6af1liOT6M0xalxLWzSU9eRz7D0eYtG41pkZPkFOmx6zWrF4g6c2XeRLzC2VuPr9Y1gl2nbQuc7c3us0QVnila4Hrh3s7ac0L4luS3ijp6iGw9SJ4tSQv7bztUyRdOST0eUmvl/RxSXO5931JT5f0rIXfnSU9QdJNx8U6p4YV8SpR79fncS9JPraP988xwXmSswB/IOmPYwo5tIT1+XrJ5KXvnO7W5an34eWpz3UurdZjW/J+PXscb25712WJ5vN2Hi+r53L7Q+P3c0q6m6S5X39h7J3XoY/bayW9RtKnNpOW+/Gy/s9jujJ3M7KYG18IK7z1PWF9czNpOeKesOZ9LX+be0KZSzr/fArgZ8vPPTlZJL7/5YvLS8NVWD6Ol4ZfkOSL9xmb5aEvvlUCU7A+37nUtHDW7aZ49u65+ZwtUb8sPkvCP3uPpKvGuRyS3BSQReAlmYXpbefPLbl5Tl6KrZOrj7fyeu6Q2d6xLGPfM/zagftT8+M3+5lSXCcsC8s858v/7X02vhBWeOtrgfND/+uRydPS9oKYE5aXjZbAA3fyf1LSv8ZF6EnrEZLuIulLkm4m6TaS7jfe521/suzDx/TE4Yv335IeMETiTaYMphjmpPKNMUF8dIjhQZL+NCa4OWn9chzHcplisNgsRU9EXgbOieaVkp43hOrj+uL2ZOhtLMD1tR7b4rFgzMTCsjyc03l9TGf76dhm3YcnLb+c569j+3XSevGQ30fGknnvI3cpYa2ievjI8+3wz+1pTx9hnZbcBXnfWuCcOCyVr48LzN/UP1yeEq7CesO4wOZ9rTlpeULyheefe9L68bhgLa/bjmlkTlivGxf2vSU9agjEk45l8lhJ95T027Hc8jTmCctCnX8ao5eSlpz36aXO9yTdZGzn999a0hclvXDn6aYFZDlYMn+T9MixhPTkZVFZZpacBeRz9TH88u/9cy8DLaS3DqGajwXs8/ON7UcPQVmM95X0inGut5T0scHHovPDBk9h9xiiXUXpY3sCfJsk30vce/BxSFjzvuTPJf1X0mPGDXhuul+QC5DTOBmB7TeOpfVlSQ8Zu1nvS/n+yyosX2i3GPer1qNub9D7d542nijpPmPfv5B0d0nzPo4FZfE8fixf5oThi/iZku4/DrDew5rvfdEQwcsl+ZwsljlZ+Vy8FH3HuH/k89guvbaTlg/lC/3T45x+JOlJY7/rFDQze8qysHxsi+E/CwyLy+fuY/rBgrNYzv+QZGn5tf79u5IeOqS+Trjebi5vPzO+TFbmW2FNqVtu8z6jv0Scw8tm/lnDya4Ttr4gBPZG5DlpedkwL5rtpOVJY71nZZltv/m3/xRi7/7OfCI3f/fVIZ/3jqXgJyTdTpKlNO8JzUlr+yRse+/NF6qnmtuPScbyW5eEawV7N9ktkjlJTcl5u71Jy/ey1vtU6wMMy8/i981uv9f3tDy5eenp/XnSetPmhv/Mup205vL10Mfn0D8/WZ8Ae9nKkvCCXICcxskIHFrTT2n5SZtf20lrFZa/sfee3nlJt4pslZJF4H1biL6457Q0pxuLZX1q5otsXuTeZm/Smhel75X5/evLN5q95POkdZJ/8Lo+wZtPCy0dT1rrPi8lrHm+/nMum2d+7+M348mrJ7R5X27yPlmbNzwcWWU+H1TMSWt7E/6kx0jenntYye1JSinQk4NfJ5HNdoLaTjLh1Z3p9FkSngkfbz4WgRRhnYaPJbc+vud/9bmBIsI6zSeK9xydwI1ZWEeHe4FPAGFd4HI4tcMEEFbnpwNhdfYenxphxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BBAWD1dkxQC8QQQVnyFBIBADwGE1dM1SSEQTwBhxVdIAAj0EEBYPV2TFALxBBBWfIUEgEAPAYTV0zVJIRBPAGHFV0gACPQQQFg9XZMUAvEEEFZ8hQSAQA8BhNXTNUkhEE8AYcVXSAAI9BD4P3NjhaYp433ZAAAAAElFTkSuQmCC"


class CustomElementRegistry(Proxy):
    pass
