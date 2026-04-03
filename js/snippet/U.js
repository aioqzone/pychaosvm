[function () {  // getattr
    var R = Y.pop();
    Y.push(R[0][R[1]])
}
    , function () {     // inst
        Y.push(B[k++])
    }
    , function () {     // stepout
        F.pop()
    }
    , function () {     // geq
        Y[Y.length - 2] = Y[Y.length - 2] >= Y.pop()
    }
    , , function () {    // copy
        Y.push(Y[Y.length - 1])
    }
    , function () {     // inv
        Y.push(!Y.pop())
    }
    , function () {     // arr_popleft
        Y[Y.length - 1].length ? Y.push(Y[Y.length - 1].shift(), !0) : Y.push(undefined, !1)
    }
    , function () {     // grwinattr
        Y.push([Q, Y.pop()])
    }
    , , function () {   // zstr
        Y.push("")
    }
    , function () {     // clear
        V = null
    }
    , , function () {   // eq
        Y[Y.length - 2] = Y[Y.length - 2] == Y.pop()
    }
    , function () {     // vm_factory
        for (var V = B[k++], A = [], R = B[k++], F = B[k++], U = [], E = 0; E < R; E++)
            A[B[k++]] = Y[B[k++]];
        for (E = 0; E < F; E++)
            U[E] = B[k++];
        Y.push(function W() {
            var R = A.slice(0);
            R[0] = [this],
                R[1] = [arguments],
                R[2] = [W];
            for (var F = 0; F < U.length && F < arguments.length; F++)
                0 < U[F] && (R[U[F]] = [arguments[F]]);
            return __TENCENT_CHAOS_VM(V, B, Q, R, C, w, J, g)
        })
    }
    , function () {     // assign
        Y[Y.length - 1] = B[k++]
    }
    , function () {     // typeof
        Y.push(typeof Y.pop())
    }
    , function () {     // outcall
        var R = B[k++]
            , F = R ? Y.slice(-R) : [];
        Y.length -= R;
        R = Y.pop();
        Y.push(R[0][R[1]].apply(R[0], F))
    }
    , function () {     // new
        var R = B[k++]
            , F = R ? Y.slice(-R) : [];
        Y.length -= R,
            F.unshift(null),
            Y.push(A(Y.pop(), F))
    }
    , function () {     // inst_arr
        Y.push([B[k++]])
    }
    , function () {     // stop
        return !0
    }
    , function () {     // swap
        var R = B[k++]
            , F = Y[Y.length - 2 - R];
        Y[Y.length - 2 - R] = Y.pop(),
            Y.push(F)
    }
    , function () {     // check_err
        return !!V
    }
    , function () {     // throw
        throw Y[Y.length - 1]
    }
    , function () {     // contains
        Y[Y.length - 2] = Y[Y.length - 2] in Y.pop()
    }
    , function () {     // setattr
        var R = Y[Y.length - 2];
        R[0][R[1]] = Y[Y.length - 1]
    }
    , function () {     // add
        Y[Y.length - 2] = Y[Y.length - 2] + Y.pop()
    }
    , function () {     // n2list
        var R = B[k++];
        Y[R] = Y[R] === undefined ? [] : Y[R]
    }
    , , function () {   // chobj
        Y[Y[Y.length - 2][0]][0] = Y[Y.length - 1]
    }
    , function () {     // getobj
        Y.push(Y[B[k++]][0])
    }
    , function () {     // refeq
        Y[Y.length - 2] = Y[Y.length - 2] === Y.pop()
    }
    , , , function () { // stepin
        F.push([B[k++], Y.length, B[k++]])
    }
    , function () { // group
        Y.push([Y.pop(), Y.pop()].reverse())
    }
    , function () {     // wincall
        var R = B[k++]
            , F = R ? Y.slice(-R) : [];
        Y.length -= R,
            Y.push(Y.pop().apply(Q, F))
    }
    , , function () {       // drop
        Y.pop()
    }
    , function () {     // undefined
        Y.push(undefined)
    }
    , function () {     // jump
        k = B[k++]
    }
    , function () {     // mul
        Y[Y.length - 2] = Y[Y.length - 2] * Y.pop()
    }
    , , , function () { // je
        var R = B[k++];
        Y[Y.length - 1] && (k = R)
    }
    , function () {     // ge
        Y[Y.length - 2] = Y[Y.length - 2] > Y.pop()
    }
    , , function () {   // rshift
        Y[Y.length - 2] = Y[Y.length - 2] >> Y.pop()
    }
    , function () {     // mod
        Y[Y.length - 2] = Y[Y.length - 2] % Y.pop()
    }
    , function () {     // delattr
        var R = Y.pop();
        Y.push(delete R[0][R[1]])
    }
    , function () {     // false
        Y.push(!1)
    }
    , function () {     // get_global
        Y[Y.length - 1] = Q[Y[Y.length - 1]]
    }
    , function () {     // bitor
        Y[Y.length - 2] = Y[Y.length - 2] | Y.pop()
    }
    , function () {     // sub
        Y[Y.length - 2] = Y[Y.length - 2] - Y.pop()
    }
    , function () {     // xor
        Y[Y.length - 2] = Y[Y.length - 2] ^ Y.pop()
    }
    , , , function () { // grobj
        var R = Y.pop();
        Y.push([Y[Y.pop()][0], R])
    }
    , function () {     // new_attr
        var R = B[k++]
            , F = R ? Y.slice(-R) : [];
        Y.length -= R,
            F.unshift(null);
        R = Y.pop();
        Y.push(A(R[0][R[1]], F))
    }
    , function () {     // true
        Y.push(!0)
    }
    , function () {     // getobj2
        Y.push(Y[Y.pop()[0]][0])
    }
    , function () {     // bitand
        Y[Y.length - 2] = Y[Y.length - 2] & Y.pop()
    }
    , function () {     // urshift
        Y[Y.length - 2] = Y[Y.length - 2] >>> Y.pop()
    }
    , function () {     // realloc
        Y.length = B[k++]
    }
    , function () {     // tolist
        var R, F = [];
        for (R in Y.pop())
            F.push(R);
        Y.push(F)
    }
    , function () {     // div
        Y[Y.length - 2] = Y[Y.length - 2] / Y.pop()
    }
    , function () {     // grgetattr
        var R = Y.pop()
            , F = Y.pop();
        Y.push([F[0][F[1]], R])
    }
    , function () {     // lshift
        Y[Y.length - 2] = Y[Y.length - 2] << Y.pop()
    }
    , function () {     // null
        Y.push(null)
    }
    , function () {     // concat
        Y[Y.length - 1] += String.fromCharCode(B[k++])
    }
]
