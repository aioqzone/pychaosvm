from gzip import decompress
from urllib.parse import unquote
from urllib.request import urlopen as get

from pytest import fixture


@fixture(
    scope="module",
    params=[
        "https://t.captcha.qq.com/tdc.js?app_data=7124050803564679168&t=636313065",
        "https://turing.captcha.qcloud.com/tdc.js?app_data=7256590633187913728",
    ],
)
def vmjs(request) -> str:
    with get(request.param) as r:
        return decompress(r.read()).decode()


def test_parse(vmjs: str):
    from chaosvm import Window, parse_vm

    stack = parse_vm(vmjs, win := Window())
    assert stack.opcode
    assert stack.opmap


def test_execute(vmjs: str):
    from chaosvm import prepare

    tdc = prepare(vmjs, "", mouse_track=[(50, 42), (50, 55)])

    info = tdc.getInfo(None)
    assert info.__dict__
    assert str(info["info"])

    collect = tdc.getData(None, True)
    collect = unquote(collect)
    assert isinstance(collect, str)
    assert len(collect) > 4
    assert "chaosvm" not in collect

    tdc = prepare(vmjs, "", mouse_track=[(50, 42), (50, 55)], return_window=True).TDC
    collect = tdc.getData(None, True)
    collect = unquote(collect)
    assert isinstance(collect, str)
    assert len(collect) > 4
    assert "chaosvm" not in collect


def test_tdc_token(vmjs: str):
    from chaosvm import prepare

    win = prepare(vmjs, "", return_window=True)
    assert win.TDC_itoken
    token1 = win.TDC_itoken

    win = prepare(vmjs, "", TDC_itoken=token1, return_window=True)
    assert win.TDC_itoken == token1
