switch (o[++K]) {
    case 0:
        R[o[++K]] = R[o[++K]] + R[o[++K]];
        break;
    case 1:
        K += R[o[++K]] ? o[++K] : o[++K,
            ++K];
        break;
    case 2:
        R[o[++K]] = "bigint" == typeof R[o[K + 1]] ? R[o[++K]] : R[o[++K]] - 0;
        break;
    case 3:
        C.push(K + o[++K]);
        break;
    case 4:
        R[o[++K]] = +R[o[++K]];
        break;
    case 5:
        R[o[++K]] = R[o[++K]] + o[++K];
        break;
    case 6:
        R[o[++K]] = R[o[++K]] == o[++K];
        break;
    case 7:
        R[o[++K]] = R[o[++K]][o[++K]];
        break;
    case 8:
        R[o[++K]] = R[o[++K]] >>> o[++K];
        break;
    case 9:
        R[o[++K]] = new R[o[++K]](R[o[++K]]);
        break;
    case 10:
        throw R[o[++K]];
        break;
    case 11:
        R[o[++K]][o[++K]] = R[o[++K]];
        return R[o[++K]];
        break;
    case 12:
        R[o[++K]] = R[o[++K]].call(Q);
        break;
    case 13:
        R[o[++K]] = R[o[++K]][R[o[++K]]];
        R[o[++K]] = R[o[++K]].call(R[o[++K]], R[o[++K]]);
        break;
    case 14:
        R[o[++K]] = R[o[++K]] > R[o[++K]];
        break;
    case 15:
        R[o[++K]] = R[o[++K]] == R[o[++K]];
        break;
    case 16:
        R[o[++K]] = R[o[++K]];
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        break;
    case 17:
        return R[o[++K]];
        break;
    case 18:
        R[o[++K]] = R[o[++K]][o[++K]];
        R[o[++K]] = R[o[++K]][o[++K]];
        break;
    case 19:
        R[o[++K]] = U;
        R[o[++K]] = R[o[++K]];
        C.push(K + o[++K]);
        break;
    case 20:
        R[o[++K]] = R[o[++K]].call(R[o[++K]], R[o[++K]], R[o[++K]], R[o[++K]]);
        break;
    case 21:
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]] += String.fromCharCode(o[++K]);
        break;
    case 22:
        R[o[++K]] = typeof R[o[++K]];
        break;
    case 23:
        R[o[++K]] = R[o[++K]] < R[o[++K]];
        break;
    case 24:
        R[o[++K]] = R[o[++K]] >> o[++K];
        break;
    case 25:
        R[o[++K]] = R[o[++K]];
        C.push(K + o[++K]);
        break;
    case 26:
        R[o[++K]] = R[o[++K]];
        break;
    case 27:
        R[o[++K]] = -R[o[++K]];
        break;
    case 28:
        R[o[++K]] = "";
        R[o[++K]] += String.fromCharCode(o[++K]);
        break;
    case 29:
        C.pop();
        break;
    case 30:
        R[o[++K]] = R[o[++K]] | o[++K];
        break;
    case 31:
        R[o[++K]] = R[o[++K]] * R[o[++K]];
        break;
    case 32:
        R[o[++K]] = R[o[++K]] << R[o[++K]];
        break;
    case 33:
        R[o[++K]] = R[o[++K]] | R[o[++K]];
        break;
    case 34:
        R[o[++K]] = R[o[++K]][R[o[++K]]];
        R[o[++K]] = o[++K];
        break;
    case 35:
        R[o[++K]] = R[o[++K]] in R[o[++K]];
        break;
    case 36:
        R[o[++K]] = !R[o[++K]];
        break;
    case 37:
        R[o[++K]] = "";
        break;
    case 38:
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        R[o[++K]] = Q;
        break;
    case 39:
        R[o[++K]] = R[o[++K]].call(R[o[++K]]);
        break;
    case 40:
        w = R[o[++K]];
        if (R[o[++K]] = !!w.length)
            R[o[++K]] = w.shift();
        else
            ++K;
        break;
    case 41:
        R[o[++K]] = R[o[++K]].call(Q, R[o[++K]]);
        R[o[++K]] = R[o[++K]];
        break;
    case 42:
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]][o[++K]] = R[o[++K]];
        break;
    case 43:
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]][o[++K]] = R[o[++K]];
        R[o[++K]] = "";
        break;
    case 44:
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]] = {};
        R[o[++K]] = "";
        break;
    case 45:
        R[o[++K]] = R[o[++K]] >= o[++K];
        break;
    case 46:
        R[o[++K]] = U;
        break;
    case 47:
        R[o[++K]] = R[o[++K]][R[o[++K]]];
        R[o[++K]] = "";
        R[o[++K]] += String.fromCharCode(o[++K]);
        break;
    case 48:
        R[o[++K]] = o[++K];
        break;
    case 49:
        R[o[++K]] = "bigint" == typeof R[o[K + 1]] ? R[o[++K]] : R[o[++K]] - 0;
        R[o[++K]] = ++R[o[++K]];
        R[o[++K]] = R[o[++K]];
        break;
    case 50:
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        R[o[++K]] = Q;
        return R[o[++K]];
        break;
    case 51:
        R[o[++K]] = Q;
        break;
    case 52:
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]] = R[o[++K]][R[o[++K]]];
        break;
    case 53:
        R[o[++K]] = R[o[++K]] === o[++K];
        break;
    case 54:
        R[o[++K]] = R[o[++K]] / R[o[++K]];
        break;
    case 55:
        R[o[++K]] = R[o[++K]] % R[o[++K]];
        break;
    case 56:
        w = [];
        for (T in R[o[++K]])
            w.push(T);
        R[o[++K]] = w;
        break;
    case 57:
        w = [];
        for (T = o[++K]; T > 0; T--)
            w.push(R[o[++K]]);
        R[o[++K]] = S(K + o[++K], w, Y, I, G);
        try {
            Object.defineProperty(R[o[K - 1]], "length", {
                value: o[++K],
                configurable: true,
                writable: false,
                enumerable: false
            })
        } catch (A) { }
        break;
    case 58:
        R[o[++K]] = R[o[++K]];
        R[o[++K]] = R[o[++K]];
        break;
    case 59:
        R[o[++K]] = R[o[++K]] & o[++K];
        break;
    case 60:
        R[o[++K]] = o[++K] - R[o[++K]];
        break;
    case 61:
        R[o[++K]] = R[o[++K]] - R[o[++K]];
        break;
    case 62:
        R[o[++K]] = new R[o[++K]];
        break;
    case 63:
        R[o[++K]] = R[o[++K]].call(Q, R[o[++K]], R[o[++K]], R[o[++K]]);
        break;
    case 64:
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]] += String.fromCharCode(o[++K]);
        R[o[++K]] += String.fromCharCode(o[++K]);
        break;
    case 65:
        R[o[++K]] = R[o[++K]].call(Q, R[o[++K]]);
        break;
    case 66:
        R[o[++K]] = null;
        break;
    case 67:
        R[o[++K]] = R[o[++K]] === R[o[++K]];
        break;
    case 68:
        w = [];
        for (T = o[++K]; T > 0; T--)
            w.push(R[o[++K]]);
        R[o[++K]] = R[o[++K]].apply(R[o[++K]], w);
        break;
    case 69:
        R[o[++K]][o[++K]] = R[o[++K]];
        break;
    case 70:
        R[o[++K]] += String.fromCharCode(o[++K]);
        w = [];
        for (T = o[++K]; T > 0; T--)
            w.push(R[o[++K]]);
        R[o[++K]] = S(K + o[++K], w, Y, I, G);
        try {
            Object.defineProperty(R[o[K - 1]], "length", {
                value: o[++K],
                configurable: true,
                writable: false,
                enumerable: false
            })
        } catch (A) { }
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        break;
    case 71:
        R[o[++K]] = R[o[++K]] << o[++K];
        break;
    case 72:
        R[o[++K]] = R[o[++K]] >> R[o[++K]];
        break;
    case 73:
        R[o[++K]] += String.fromCharCode(o[++K]);
        break;
    case 74:
        R[o[++K]] = delete R[o[++K]][R[o[++K]]];
        break;
    case 75:
        w = [];
        for (T = o[++K]; T > 0; T--)
            w.push(R[o[++K]]);
        R[o[++K]] = S(K + o[++K], w, Y, I, G);
        try {
            Object.defineProperty(R[o[K - 1]], "length", {
                value: o[++K],
                configurable: true,
                writable: false,
                enumerable: false
            })
        } catch (A) { }
        R[o[++K]][o[++K]] = R[o[++K]];
        w = [];
        for (T = o[++K]; T > 0; T--)
            w.push(R[o[++K]]);
        R[o[++K]] = S(K + o[++K], w, Y, I, G);
        try {
            Object.defineProperty(R[o[K - 1]], "length", {
                value: o[++K],
                configurable: true,
                writable: false,
                enumerable: false
            })
        } catch (A) { }
        break;
    case 76:
        K += o[++K];
        break;
    case 77:
        R[o[++K]][o[++K]] = R[o[++K]];
        w = [];
        for (T = o[++K]; T > 0; T--)
            w.push(R[o[++K]]);
        R[o[++K]] = S(K + o[++K], w, Y, I, G);
        try {
            Object.defineProperty(R[o[K - 1]], "length", {
                value: o[++K],
                configurable: true,
                writable: false,
                enumerable: false
            })
        } catch (A) { }
        R[o[++K]][o[++K]] = R[o[++K]];
        break;
    case 78:
        R[o[++K]] = R[o[++K]].call(R[o[++K]], R[o[++K]], R[o[++K]]);
        break;
    case 79:
        R[o[++K]] = R[o[++K]] - o[++K];
        break;
    case 80:
        R[o[++K]] = o[++K];
        R[o[++K]] = R[o[++K]].call(Q, R[o[++K]]);
        R[o[++K]] = R[o[++K]];
        break;
    case 81:
        R[o[++K]] = R[o[++K]] > o[++K];
        break;
    case 82:
        R[o[++K]] = R[o[++K]].call(R[o[++K]], R[o[++K]]);
        break;
    case 83:
        R[o[++K]] = ++R[o[++K]];
        break;
    case 84:
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        break;
    case 85:
        R[o[++K]] = Array(o[++K]);
        break;
    case 86:
        R[o[++K]] = {};
        break;
    case 87:
        R[o[++K]] = R[o[++K]] ^ R[o[++K]];
        break;
    case 88:
        R[o[++K]] = R[o[++K]] < o[++K];
        break;
    case 89:
        R[o[++K]] = new R[o[++K]](R[o[++K]], R[o[++K]]);
        break;
    case 90:
        R[o[++K]][R[o[++K]]] = R[o[++K]];
        R[o[++K]] = R[o[++K]][R[o[++K]]];
        R[o[++K]] = o[++K];
        break;
    case 91:
        R[o[++K]] = R[o[++K]][R[o[++K]]];
        break;
    case 92:
        R[o[++K]] = --R[o[++K]];
        break;
    case 93:
        R[o[++K]] = Q;
        return R[o[++K]];
        break;
    case 94:
        R[o[++K]] = R[o[++K]].call(Q, R[o[++K]], R[o[++K]]);
        break;
    case 95:
        R[o[++K]] = R[o[++K]] <= o[++K];
        break
}
