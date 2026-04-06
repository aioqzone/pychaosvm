import re
from base64 import b64decode
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

import pyjsparser as jsparser

from chaosvm.opfeats import FUNARR_OP_FEATS, SWITCH_OP_FEATS
from chaosvm.proxy.dom import Date, Window
from chaosvm.stack import ChaosStack
from chaosvm.stxhash import syntax_feat, syntax_hash


def path_get(d: Union[dict, list], *path: Union[str, int]) -> Any:
    o = d
    for i in path:
        o = o[i]  # type: ignore
    return o


def path_get_default(d: Union[dict, list], *path: Union[str, int], default=None) -> Any:
    o = d
    for i in path:
        if (isinstance(o, dict) and i not in o) or (
            isinstance(o, list) and i >= len(o)  # type: ignore
        ):
            return default
        o = o[i]  # type: ignore
    return o


def first(pred: Callable, it: Iterable):
    return next(filter(pred, it))


def detect_vm_type(*ast) -> str:
    """Detect VM type from VM AST.

    :param ast: Variable length AST nodes to analyze
    :return: VM type identifier - 'funarr' for array-based function dispatch or 'switch' for switch-case dispatch
    :raises NotImplementedError: if VM type cannot be detected from the provided AST
    """
    for tree in ast:
        match tree:
            case {
                "type": "ExpressionStatement",
                "expression": {"left": {"object": {"name": "__TENCENT_CHAOS_STACK"}}},
            }:
                return "funarr"
            case {
                "type": "VariableDeclaration",
                "declarations": [{"id": {"name": "__TENCENT_CHAOS_VM"}}],
            }:
                return "switch"

    raise NotImplementedError("cannot detect VM type :(")


def parse_vm(vm_js: str, window: Window, vm_type: str = "auto"):
    """Parse VM from JavaScript source and initialize the VM stack.

    :param vm_js: The JavaScript VM source code to parse
    :param window: The Window object to use as global execution context
    :param vm_type: VM type - 'funarr', 'switch', or 'auto' for auto-detection (defaults to 'auto')
    :return: Initialized ChaosStack ready for execution
    :raises NotImplementedError: if VM type cannot be auto-detected
    :raises RuntimeError: if VM declaration or call expression cannot be found
    """
    ast = jsparser.parse(vm_js)
    assert isinstance(ast, dict)

    bodies = [i for i in ast["body"] if isinstance(i, dict) and i["type"] != "EmptyStatement"]

    if vm_type == "auto":
        vm_type = detect_vm_type(*bodies)

    nonliterals = []
    for i in bodies:
        match i:
            case {
                "type": "ExpressionStatement",
                "expression": {
                    "right": {"type": "Literal", "raw": rval},
                    "left": {"property": {"name": lval}},
                },
            }:
                window[lval] = rval
                continue
            case dict():
                nonliterals.append(i)

    # assign Date alias into window
    date_hashes = {}
    for i in nonliterals:
        if i["type"] == "ExpressionStatement":
            expr = i["expression"]
            # Only process assignment expressions (left = right)
            if expr["type"] == "AssignmentExpression":
                c: defaultdict = defaultdict(lambda: f"t{len(c)}")
                try:
                    right = path_get(expr, "right")
                    left_prop = path_get(expr, "left", "property", "name")
                    h = syntax_feat(right, c)
                    date_hashes[h] = left_prop
                except (KeyError, TypeError):
                    continue
    window[date_hashes["fun(){return new Date()}"]] = Date
    window[date_hashes["fun(t0,t1){return Date[t0][apply](Date,t1)}"]] = lambda attr, args: (
        getattr(Date, attr)(*args)
    )

    if vm_type == "funarr":
        stack_dcl = first(
            lambda i: (
                i["type"] == "VariableDeclaration"
                and path_get(i, "declarations", 0, "id", "name") == "__TENCENT_CHAOS_STACK"
            ),
            bodies,
        )
        stack_bodies = path_get(stack_dcl, "declarations", 0, "init", "callee", "body", "body")

        stack_ret = first(lambda i: i["type"] == "ReturnStatement", stack_bodies)
        ret_expr = path_get(stack_ret, "argument", "expressions")

        outer_vm = first(lambda i: i["type"] == "CallExpression", ret_expr)
        pc, al_core = outer_vm["arguments"][:2]
        pc = int(pc["raw"])

        data, opdata = path_get(al_core, "arguments", 0, "elements")

        # Decode opcodes based on VM type
        opcodes = parse_opcodes(data["raw"], [int(i["value"]) for i in opdata["elements"]])

        vm_dcl = first(
            lambda i: (
                i["type"] == "FunctionDeclaration"
                and path_get(i, "id", "name") == "__TENCENT_CHAOS_VM"
            ),
            stack_bodies,
        )
    else:
        # Switch VM: extract from __TENCENT_CHAOS_VM function and its call expression
        # Find the VM function declaration (could be VariableDeclaration with function expression)
        vm_dcl = None
        for node in bodies:
            if (
                node["type"] == "FunctionDeclaration"
                and path_get(node, "id", "name") == "__TENCENT_CHAOS_VM"
            ):
                vm_dcl = node
                break
            elif node["type"] == "VariableDeclaration":
                for decl in node.get("declarations", []):
                    if path_get(decl, "id", "name") == "__TENCENT_CHAOS_VM":
                        # The function is in init.callee (FunctionExpression)
                        init = decl.get("init")
                        if init and init.get("type") == "CallExpression":
                            callee = init.get("callee", {})
                            if callee.get("type") == "FunctionExpression":
                                # Create a synthetic function declaration node
                                vm_dcl = {
                                    "type": "FunctionDeclaration",
                                    "id": {"name": "__TENCENT_CHAOS_VM"},
                                    "params": callee.get("params", []),
                                    "body": callee.get("body", {"body": []}),
                                }
                                break
                if vm_dcl:
                    break

        # Find the VM call expression to extract encoded data and PC
        # Pattern: __TENCENT_CHAOS_VM("base64_data", false)(pc, [], window, ...)()
        vm_call = None
        for stmt in bodies:
            if stmt["type"] == "ExpressionStatement":
                expr = stmt["expression"]
                # Check for chained call with multiple levels
                # Could be: CallExpression(CallExpression(CallExpression(Identifier)))
                if expr["type"] == "CallExpression":
                    # Walk down the callee chain to find __TENCENT_CHAOS_VM
                    call_chain = [expr]
                    current = expr
                    while current["type"] == "CallExpression":
                        callee = current["callee"]
                        if (
                            callee["type"] == "Identifier"
                            and callee.get("name") == "__TENCENT_CHAOS_VM"
                        ):
                            # Found it!
                            # call_chain[0] = outermost call (no args)
                            # call_chain[1] = middle call (with PC, [], window...)
                            # call_chain[-1] = innermost call (with "data", false)
                            inner_call = call_chain[-1]  # __TENCENT_CHAOS_VM("data", false)
                            outer_call = call_chain[1] if len(call_chain) > 1 else call_chain[0]
                            vm_call = (inner_call, outer_call)
                            break
                        elif callee["type"] == "CallExpression":
                            call_chain.append(callee)
                            current = callee
                        else:
                            break
                    if vm_call:
                        break

        if vm_dcl is None:
            raise RuntimeError("Could not find __TENCENT_CHAOS_VM declaration")

        if vm_call is None:
            raise RuntimeError("Could not find __TENCENT_CHAOS_VM call")

        inner_call, outer_call = vm_call

        # Extract base64 encoded opcode data from inner call
        data_arg = inner_call["arguments"][0]
        if data_arg["type"] == "Literal":
            encoded_data = data_arg["value"]
        else:
            raise RuntimeError("Expected literal for VM data")

        # Decode switch-style opcodes
        opcodes = parse_switch_opcodes(encoded_data)

        # Extract PC from outer call's first argument
        pc_arg = outer_call["arguments"][0]
        if pc_arg["type"] == "Literal":
            pc = int(pc_arg["value"])
        else:
            pc = 0  # Default PC

    # Store vm_type for later use
    stack = ChaosStack(parse_opcode_mapping(vm_dcl, vm_type), opcodes, pc=pc, vm_type=vm_type)
    window.__TENCENT_CHAOS_STACK = stack
    return stack


declare_parsers = [
    lambda dcl_content: [
        i
        for d in dcl_content
        if d["type"] == "VariableDeclaration"
        and (i := path_get_default(d, "declarations", 0, "init"))
    ],
    lambda dcl_content: [
        i
        for d in dcl_content
        if d["type"] == "ForStatement"
        and (i := path_get_default(d, "init", "declarations", 0, "init"))
    ],
]


def try_get_declare_contents(vm_declare: dict) -> Tuple[int, List[dict]]:
    for ver, f in enumerate(declare_parsers):
        if dcl := f(vm_declare):
            return ver, dcl
    raise NotImplementedError("This version is not tested...")


def parse_opcode_mapping(vm_declare: dict, vm_type: str = "funarr") -> Dict[int, int]:
    """Parse operation-code mapping from VM declaration.

    :param vm_declare: The VM function declaration AST node
    :param vm_type: VM implementation style - 'funarr' or 'switch' (defaults to 'funarr')
    :return: Mapping from operation indices to their implementation opcodes
    :raises RuntimeError: if operation feature hash mismatches the expected features
    :raises NotImplementedError: if the VM declaration version is not supported
    """
    params = vm_declare["params"]

    if vm_type == "switch":
        # For switch VM, we need to map case numbers to operation indices
        # The opmap is typically embedded in the function or can be inferred
        # For now, create an identity mapping with feature verification
        G = {i["name"]: k for i, k in zip(params, ["g", "E", "Y", "I", "G"])}
        # Try to find switch statement and extract cases
        func_body = path_get(vm_declare, "body", "body")
        for stmt in func_body:
            if stmt["type"] == "WhileStatement":
                try_stmt = stmt["body"]
                if try_stmt["type"] == "TryStatement":
                    try_block = path_get(try_stmt, "block", "body")
                    for stmt2 in try_block:
                        if stmt2["type"] == "WhileStatement":
                            switch_stmt = stmt2["body"]
                            if switch_stmt["type"] == "SwitchStatement":
                                # Build mapping from case numbers to operation indices
                                d: Dict[int, int] = {}
                                cases = switch_stmt["cases"]
                                for i, case in enumerate(cases):
                                    case_num = case["test"]["value"] if case["test"] else None
                                    if case_num is not None:
                                        case_num = int(case_num)
                                        # Verify feature matches
                                        c = defaultdict(lambda: f"t{len(c)}", G)
                                        h = syntax_hash(case["consequent"], c)
                                        if h in SWITCH_OP_FEATS:
                                            d[case_num] = SWITCH_OP_FEATS.index(h)
                                        else:
                                            # Unknown case - map to itself
                                            d[case_num] = case_num
                                return d
        # Fallback to identity mapping
        return {i: i for i in range(96)}

    # Funarr style (original)
    G = {i["name"]: k for i, k in zip(params, ["p", "P", "window", "S"])}

    version, declares = try_get_declare_contents(path_get(vm_declare, "body", "body"))
    op_def_list = first(lambda i: i["type"] == "ArrayExpression", declares)["elements"]

    d: Dict[int, int] = {}
    for i, func in enumerate(op_def_list):
        if func is not None:
            c = defaultdict(lambda: f"t{len(c) - 4}", G)
            node = path_get(func, "body", "body")
            h = syntax_hash(node, c)
            if h not in FUNARR_OP_FEATS:
                raise RuntimeError("op feature mismatch", node)
            d[i] = FUNARR_OP_FEATS.index(h)
    return d


def parse_opcodes(b64: str, arr: List[int]) -> List[int]:
    """Parse funarr-style opcodes from base64-encoded data.

    :param b64: Base64-encoded opcode data (standard base64)
    :param arr: Array of [escape_code, value, ...] pairs for escape sequence handling
    :return: Decoded list of opcodes
    """
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


def parse_switch_opcodes(b64: str) -> List[int]:
    """Parse switch-style opcodes from encoded data.

    Decoding process:
        1. Custom Base64 decoding using E array
        2. Varint decoding (7-bit chunks with continuation)
        3. Zigzag decoding for signed integers

    :param b64: Base64-encoded opcode data (custom base64 + varint + zigzag encoding)
    :return: Decoded list of opcodes as signed integers
    """

    # Custom Base64 decoding table from switch.js
    def build_decode_table() -> List[int]:
        """Build the E array used in switch.js base64 decoding."""
        E = []
        # Generate the pattern: 43 zeros, then [62, 0, 62, 0, 63],
        # then g(51, 10, 1), then zeros, then g(0, 25, 1), etc.
        E.extend([0] * 43)
        E.extend([62, 0, 62, 0, 63])
        # g(51, 10, 1): start at 51, 10 elements, step 1
        E.extend([51 + i for i in range(10)])
        E.extend([0] * 8)
        # g(0, 25, 1): 0 to 24
        E.extend([i for i in range(25)])
        E.extend([0, 0, 0, 0, 63, 0])
        # g(25, 26, 1): 25 to 50
        E.extend([25 + i for i in range(26)])
        return E

    E = build_decode_table()

    # Base64 decode
    B64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    b64_clean = b64.rstrip("=")

    decoded_bytes: List[int] = []
    Y, I = 0, 0
    for G, char in enumerate(b64_clean):
        S = E[ord(char)] if ord(char) < len(E) else -1
        if S == -1:
            continue
        if I % 4:
            Y = 64 * Y + S
            decoded_bytes.append(255 & Y >> (-2 * I & 6))
        else:
            Y = S
        I += 1

    # Varint + Zigzag decode
    def zigzag_decode(n: int) -> int:
        """Zigzag decoding: value >> 1 ^ -(value & 1)"""
        return n >> 1 ^ -(n & 1)

    result: List[int] = []
    S_pos = 0
    while S_pos < len(decoded_bytes):
        I = decoded_bytes[S_pos]
        S_pos += 1
        G = 127 & I

        if I < 0x80:  # Positive means no more bytes
            result.append(zigzag_decode(G))
            continue

        # Need more bytes
        for shift in [7, 14, 21, 28]:
            if S_pos >= len(decoded_bytes):
                break
            I = decoded_bytes[S_pos]
            S_pos += 1
            G |= (127 & I) << shift
            if I < 0x80:
                break

        result.append(zigzag_decode(G))

    return result
