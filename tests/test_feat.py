from collections import defaultdict

from pyjsparser import parse

from chaosvm.stxhash import syntax_hash


def test_new_attr():
    G1 = dict(C="p", y="P", Q="window", H="S")
    G2 = dict(k="p", B="P", Q="window", Y="S")
    s1 = """
    var B = y[C++]
        , g = B ? H.slice(-B) : []
        , B = (H.length -= B,
    g.unshift(null),
    H.pop());
    H.push(A(B[0][B[1]], g))
    """
    s2 = """
    var R = B[k++]
        , F = R ? Y.slice(-R) : [];
    Y.length -= R,
        F.unshift(null);
    R = Y.pop();
    Y.push(A(R[0][R[1]], F))
    """
    ast1 = parse(s1)
    ast2 = parse(s2)

    assert isinstance(ast1, dict)
    assert isinstance(ast2, dict)

    c = defaultdict(lambda: f"t{len(c) - 4}", G1)
    f1 = syntax_hash(ast1["body"], c)

    c = defaultdict(lambda: f"t{len(c) - 4}", G2)
    f2 = syntax_hash(ast2["body"], c)

    assert f1
    assert f1 == f2
