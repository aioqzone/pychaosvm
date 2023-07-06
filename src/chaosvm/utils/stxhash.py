from ast import literal_eval
from collections import defaultdict
from typing import Optional, Union


def _syntax_hash(node: dict, context: defaultdict, d=";"):
    cases = dict(
        Literal=lambda: defaultdict(lambda: repr(literal_eval(c)), dict(null="null"))[
            (c := node["raw"])
        ],
        Identifier=lambda: context[c] if len(c := node["name"]) == 1 else c,
        VariableDeclaration=lambda: f"{node['kind']} {syntax_hash(node['declarations'], context, ',')}",
        VariableDeclarator=lambda: f"{syntax_hash(node['id'], context)}={syntax_hash(node['init'], context)}"
        if node["init"]
        else syntax_hash(node["id"], context),
        AssignmentExpression=lambda: f"{syntax_hash(node['left'], context)}"
        f"{node['operator']}{syntax_hash(node['right'], context)}",
        UnaryExpression=lambda: f"{node['operator']}{syntax_hash(node['argument'], context)}",
        BinaryExpression=lambda: f"{syntax_hash(node['left'], context)}"
        f"{node['operator']}{syntax_hash(node['right'], context)}",
        UpdateExpression=lambda: "^" if node["prefix"] else "" + node["operator"],
        ArrayExpression=lambda: f"[{syntax_hash(node['elements'], context)}]",
        CallExpression=lambda: f"{syntax_hash(node['callee'], context)}"
        f"({syntax_hash(node['arguments'], context, ',')})",
        MemberExpression=lambda: f"{syntax_hash(node['object'], context)}"
        f"[{syntax_hash(node['property'], context)}]",
        ExpressionStatement=lambda: syntax_hash(node["expression"], context),
        SequenceExpression=lambda: syntax_hash(node["expressions"], context, ","),
        ForStatement=lambda: "for",
        ForInStatement=lambda: "for in",
        ConditionalExpression=lambda: f"{syntax_hash(node['test'], context)}?"
        f"({syntax_hash(node['consequent'], context)}):({syntax_hash(node['alternate'], context)})",
        ReturnStatement=lambda: f"return {syntax_hash(node['argument'], context)}",
        ThrowStatement=lambda: f"throw {syntax_hash(node['argument'], context)}",
    )
    yield defaultdict(lambda: str, cases)[node["type"]]()


def syntax_hash(node: Union[list, dict], context: defaultdict, d=";"):
    if isinstance(node, list):
        return d.join(syntax_hash(i, context, d) for i in node)

    return "".join(_syntax_hash(node, context, d))


if __name__ == "__main__":
    from hashlib import md5

    from pyjsparser import parse

    from chaosvm.parse import path_get

    with open("js/snippet/U.js", encoding="utf8") as f:
        ls_md5 = []
        G = dict(k="p", B="P", Q="window", Y="S")
        ast = parse(f.read())

        for i, func in enumerate(path_get(ast, "body", 0, "expression", "elements")):
            if func is None:
                continue
            c = defaultdict(lambda: f"t{len(c)-4}", G)
            feat = syntax_hash(path_get(func, "body", "body"), c)
            ls_md5.append(md5(feat.encode()).hexdigest())

        print(len(ls_md5))
        print(tuple(ls_md5))
