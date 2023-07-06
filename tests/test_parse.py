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
    from chaosvm import execute

    tdc = execute(vmjs)
    assert tdc.getInfo().__dict__
    assert tdc.getData(None, True)
