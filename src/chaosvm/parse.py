from base64 import b64decode
from collections import defaultdict
from hashlib import md5
from typing import Any, Callable, Dict, Iterable, List, Union

import pyjsparser as jsparser

from chaosvm.proxy.dom import Date, Window
from chaosvm.stack import ChaosStack
from chaosvm.stxhash import syntax_hash
from chaosvm.vm import OP_FEATS


def path_get(d: Union[dict, list], *path: Union[str, int]) -> Any:
    o = d
    for i in path:
        o = o[i]  # type: ignore
    return o


def first(pred: Callable, it: Iterable):
    return next(filter(pred, it))


def parse_vm(vm_js: str, window: Window):
    ast = jsparser.parse(vm_js)
    assert isinstance(ast, dict)

    bodies = [i for i in ast["body"] if i["type"] != "EmptyStatement"]

    new_date = path_get(bodies, 0, "expression", "left", "property", "name")
    window[new_date] = Date
    date_attr = path_get(bodies, 1, "expression", "left", "property", "name")
    window[date_attr] = lambda attr, args: getattr(Date, attr)(*args)
    win_attr = path_get(bodies, 2, "expression", "left", "property", "name")
    window[win_attr] = path_get(bodies, 2, "expression", "right", "raw")

    stack_dcl = first(
        lambda i: i["type"] == "VariableDeclaration"
        and path_get(i, "declarations", 0, "id", "name") == "__TENCENT_CHAOS_STACK",
        bodies,
    )
    stack_bodies = path_get(stack_dcl, "declarations", 0, "init", "callee", "body", "body")

    stack_ret = first(lambda i: i["type"] == "ReturnStatement", stack_bodies)
    ret_expr = path_get(stack_ret, "argument", "expressions")

    outer_vm = first(lambda i: i["type"] == "CallExpression", ret_expr)
    pc, al_core = outer_vm["arguments"][:2]
    pc = int(pc["raw"])

    data, opdata = path_get(al_core, "arguments", 0, "elements")
    opcodes = parse_opcodes(data["raw"], [int(i["value"]) for i in opdata["elements"]])

    vm_dcl = first(
        lambda i: i["type"] == "FunctionDeclaration"
        and path_get(i, "id", "name") == "__TENCENT_CHAOS_VM",
        stack_bodies,
    )

    stack = ChaosStack(parse_opcode_mapping(vm_dcl), opcodes, pc=pc)
    window.__TENCENT_CHAOS_STACK = stack
    return stack


def parse_opcode_mapping(vm_declare: dict) -> Dict[int, int]:
    """Parse operation-code mapping."""
    params = vm_declare["params"]
    G = {i["name"]: k for i, k in zip(params, ["p", "P", "window", "S"])}
    dcl_content = path_get(vm_declare, "body", "body")
    declares = [
        i
        for d in dcl_content
        if d["type"] == "VariableDeclaration" and (i := path_get(d, "declarations", 0, "init"))
    ]
    op_def_list = first(lambda i: i["type"] == "ArrayExpression", declares)["elements"]

    d: Dict[int, int] = {}
    for i, func in enumerate(op_def_list):
        if func is not None:
            c = defaultdict(lambda: f"t{len(c)-4}", G)
            feat = syntax_hash(path_get(func, "body", "body"), c)
            h = md5(feat.encode()).hexdigest()
            d[i] = OP_FEATS.index(h)
    return d


def parse_opcodes(b64: str, arr: List[int]) -> List[int]:
    ret: List[int] = []
    data = b64decode(b64.rstrip("="))
    arr += [None] * 2  # type: ignore
    k, E, W = 0, arr.pop(0), arr.pop(0)

    for c in data:
        while k == E:
            ret.append(W)
            k += 1
            E, W = arr.pop(0), arr.pop(0)

        ret.append(c)
        k += 1

    while k == E:
        ret.append(W)
        k += 1
        E, W = arr.pop(0), arr.pop(0)

    return ret


if __name__ == "__main__":
    from chaosvm.proxy.dom import Window

    win = Window()
    win.add_mouse_track([(50, 42), (50, 55)])
    with open("js/vm.js.bak", encoding="utf8") as f:
        parse_vm(f.read(), win)(win)
        print(win.TDC.getInfo().__dict__)
        print(win.TDC.getData(None, True))
