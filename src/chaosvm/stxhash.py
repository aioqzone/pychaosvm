from ast import literal_eval
from collections import defaultdict
from hashlib import md5


def syntax_feat(node: list | dict, context: defaultdict[str, str], delimiter=";") -> str:
    """Generate a normalized syntax hash string from a pyjsparser AST node.

    The hash string is used to identify ChaosVM operations by their syntax
    structure. Variable names are normalized via *context*.

    :param node: A pyjsparser AST node (dict) or a list of nodes.
    :param context: A mapping used to normalize variable names.
    :param delimiter: Delimiter used when joining list elements. Defaults to ``";"``.
    :return: The normalized syntax hash string.
    """
    if isinstance(node, list):
        return delimiter.join(syntax_feat(i, context, delimiter) for i in node)

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
            return syntax_feat(node["declarations"], context)
        case "VariableDeclarator":
            id_hash = syntax_feat(node["id"], context)
            if node["init"]:
                if node["init"]["type"] == "SequenceExpression":
                    return (
                        syntax_feat(node["init"]["expressions"][:-1], context)
                        + delimiter
                        + f"{id_hash}={syntax_feat(node['init']['expressions'][-1], context)}"
                    )
                return f"{id_hash}={syntax_feat(node['init'], context)}"
            return ""
        case "AssignmentExpression":
            return (
                f"{syntax_feat(node['left'], context)}"
                f"{node['operator']}{syntax_feat(node['right'], context)}"
            )
        case "UnaryExpression":
            return f"{node['operator']}{syntax_feat(node['argument'], context)}"
        case "BinaryExpression":
            return (
                f"{syntax_feat(node['left'], context)}"
                f"{node['operator']}{syntax_feat(node['right'], context)}"
            )
        case "UpdateExpression":
            return ("^" if node["prefix"] else "") + node["operator"]
        case "ArrayExpression":
            return f"[{syntax_feat(node['elements'], context, ',')}]"
        case "CallExpression":
            return (
                f"{syntax_feat(node['callee'], context)}"
                f"({syntax_feat(node['arguments'], context, ',')})"
            )
        case "NewExpression":
            return f"new {syntax_feat(node['callee'], context)}()"
        case "MemberExpression":
            return (
                f"{syntax_feat(node['object'], context)}[{syntax_feat(node['property'], context)}]"
            )
        case "ExpressionStatement":
            return syntax_feat(node["expression"], context)
        case "SequenceExpression":
            return syntax_feat(node["expressions"], context)
        case "ForStatement":
            return "for"
        case "ForInStatement":
            return "for in"
        case "ConditionalExpression":
            return (
                f"{syntax_feat(node['test'], context)}?"
                f"({syntax_feat(node['consequent'], context)}):"
                f"({syntax_feat(node['alternate'], context)})"
            )
        case "ReturnStatement":
            return f"return {syntax_feat(node['argument'], context)}"
        case "ThrowStatement":
            return f"throw {syntax_feat(node['argument'], context)}"
        case "FunctionExpression":
            id_part = "" if node["id"] is None else " " + syntax_feat(node["id"], context)
            params = ",".join(syntax_feat(p, context) for p in node["params"])
            return f"fun{id_part}({params}){syntax_feat(node['body'], context)}"
        case "BlockStatement":
            return f"{{{syntax_feat(node['body'], context)}}}"
        case _:
            return ""


def syntax_hash(node: list | dict, context: defaultdict[str, str], delimiter=";") -> str:
    return md5(syntax_feat(node, context, delimiter=delimiter).encode()).hexdigest()
