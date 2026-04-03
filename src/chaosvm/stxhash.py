from ast import literal_eval
from collections import defaultdict


def syntax_hash(node: list | dict, context: defaultdict[str, str], delimiter=";") -> str:
    """Generate a normalized syntax hash string from a pyjsparser AST node.

    The hash string is used to identify ChaosVM operations by their syntax
    structure. Variable names are normalized via *context*.

    :param node: A pyjsparser AST node (dict) or a list of nodes.
    :param context: A mapping used to normalize variable names.
    :param delimiter: Delimiter used when joining list elements. Defaults to ``";"``.
    :return: The normalized syntax hash string.
    """
    if isinstance(node, list):
        return delimiter.join(syntax_hash(i, context, delimiter) for i in node)

    match node["type"]:
        case "Literal":
            raw = node["raw"]
            if raw == "null":
                return "null"
            return repr(literal_eval(raw))
        case "Identifier":
            c = node["name"]
            return context[c] if len(c) == 1 else c
        case "VariableDeclaration":
            return syntax_hash(node["declarations"], context)
        case "VariableDeclarator":
            id_hash = syntax_hash(node["id"], context)
            if node["init"]:
                if node["init"]["type"] == "SequenceExpression":
                    return (
                        syntax_hash(node["init"]["expressions"][:-1], context)
                        + delimiter
                        + f"{id_hash}={syntax_hash(node['init']['expressions'][-1], context)}"
                    )
                return f"{id_hash}={syntax_hash(node['init'], context)}"
            return ""
        case "AssignmentExpression":
            return (
                f"{syntax_hash(node['left'], context)}"
                f"{node['operator']}{syntax_hash(node['right'], context)}"
            )
        case "UnaryExpression":
            return f"{node['operator']}{syntax_hash(node['argument'], context)}"
        case "BinaryExpression":
            return (
                f"{syntax_hash(node['left'], context)}"
                f"{node['operator']}{syntax_hash(node['right'], context)}"
            )
        case "UpdateExpression":
            return ("^" if node["prefix"] else "") + node["operator"]
        case "ArrayExpression":
            return f"[{syntax_hash(node['elements'], context, ',')}]"
        case "CallExpression":
            return (
                f"{syntax_hash(node['callee'], context)}"
                f"({syntax_hash(node['arguments'], context, ',')})"
            )
        case "NewExpression":
            return f"new {syntax_hash(node['callee'], context)}()"
        case "MemberExpression":
            return (
                f"{syntax_hash(node['object'], context)}[{syntax_hash(node['property'], context)}]"
            )
        case "ExpressionStatement":
            return syntax_hash(node["expression"], context)
        case "SequenceExpression":
            return syntax_hash(node["expressions"], context)
        case "ForStatement":
            return "for"
        case "ForInStatement":
            return "for in"
        case "ConditionalExpression":
            return (
                f"{syntax_hash(node['test'], context)}?"
                f"({syntax_hash(node['consequent'], context)}):"
                f"({syntax_hash(node['alternate'], context)})"
            )
        case "ReturnStatement":
            return f"return {syntax_hash(node['argument'], context)}"
        case "ThrowStatement":
            return f"throw {syntax_hash(node['argument'], context)}"
        case "FunctionExpression":
            id_part = "" if node["id"] is None else " " + syntax_hash(node["id"], context)
            params = ",".join(syntax_hash(p, context) for p in node["params"])
            return f"fun{id_part}({params}){syntax_hash(node['body'], context)}"
        case "BlockStatement":
            return f"{{{syntax_hash(node['body'], context)}}}"
        case _:
            return ""


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
            c = defaultdict(lambda: f"t{len(c) - 4}", G)
            feat = syntax_hash(path_get(func, "body", "body"), c)
            ls_md5.append(md5(feat.encode()).hexdigest())

        print(len(ls_md5))
        print(tuple(ls_md5))
