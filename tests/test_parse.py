from gzip import decompress
from urllib.request import urlopen as get

from pytest import fixture


@fixture(scope="module")
def vmjs():
    with get("https://t.captcha.qq.com/tdc.js?app_data=7082613120539107328&t=939066183") as r:
        return decompress(r.read()).decode()


def test_parse(vmjs: str):
    from chaosvm import Window, parse_vm

    stack = parse_vm(vmjs, win := Window())
    assert stack.opcode
    assert len(stack.opmap) == 58


def test_execute(vmjs: str):
    from chaosvm import prepare

    tdc = prepare(vmjs, "", mouse_track=[(50, 42), (50, 55)])

    info = tdc.getInfo().__dict__
    assert info
    assert info["info"]

    collect = tdc.getData(None, True)
    assert isinstance(collect, str)
    assert len(collect) > 4
