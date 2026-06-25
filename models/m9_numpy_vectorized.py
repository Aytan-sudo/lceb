"""Modèle 9 — Reachability vectorisée NumPy (origine : main9_improved.py).

Phase 1 vectorisée : les opérations entre les valeurs atteignables de deux
moitiés sont calculées par grilles NumPy (broadcasting) au lieu de boucles
Python imbriquées. Phase 2 : reconstruction ciblée identique au modèle 8.

Note : le ``multiprocessing`` de l'original a été retiré. À n ≤ 9 le coût de
spawn/pickle dépassait tout gain, et le ``Pool`` sans garde rendait le module
fragile à l'import. La vectorisation NumPy reste la caractéristique distinctive.
"""

from functools import lru_cache

import numpy as np

from . import _render as R
from ._masks import partitions_by_mask

NAME = "numpy_vectorized"
ORIGIN = "main9_improved.py"
DESCRIPTION = "Reachability vectorisée NumPy + reconstruction ciblée (multiprocessing retiré)."


def _vectorized_ops(valsA, valsB):
    a = np.array(sorted(valsA), dtype=np.int64)
    b = np.array(sorted(valsB), dtype=np.int64)
    res = set()

    res.update((a[:, None] + b[None, :]).flatten().tolist())
    res.update((a[:, None] * b[None, :]).flatten().tolist())

    sub1 = a[:, None] - b[None, :]
    res.update(sub1[sub1 > 0].tolist())
    sub2 = b[None, :] - a[:, None]
    res.update(sub2[sub2 > 0].tolist())

    with np.errstate(divide="ignore", invalid="ignore"):
        m1 = (b[None, :] != 0) & (a[:, None] % b[None, :] == 0)
        q1 = np.where(m1, a[:, None] // np.where(b[None, :] == 0, 1, b[None, :]), 0)
        res.update(q1[m1 & (q1 > 0)].tolist())

        m2 = (a[:, None] != 0) & (b[None, :] % np.where(a[:, None] == 0, 1, a[:, None]) == 0)
        q2 = np.where(m2, b[None, :] // np.where(a[:, None] == 0, 1, a[:, None]), 0)
        res.update(q2[m2 & (q2 > 0)].tolist())

    return res


def solve(nombres, cible):
    n = len(nombres)
    max_mask = 1 << n
    full = max_mask - 1
    parts = partitions_by_mask(n)

    reachable = [None] * max_mask
    for i, v in enumerate(nombres):
        reachable[1 << i] = frozenset((v,))

    for mask in range(1, max_mask):
        if reachable[mask] is not None:
            continue
        vals = set()
        for A, B in parts[mask]:
            vals.update(_vectorized_ops(reachable[A], reachable[B]))
        reachable[mask] = frozenset(vals)

    if cible not in reachable[full]:
        return set()

    @lru_cache(maxsize=None)
    def build_exprs(mask, value):
        if not (mask & (mask - 1)):
            v = nombres[mask.bit_length() - 1]
            return frozenset((R.feuille(v),)) if v == value else frozenset()

        exprs = set()
        for A, B in parts[mask]:
            sA, sB = reachable[A], reachable[B]

            for x in sA:
                y = value - x
                if y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.add(ea, eb))
            for x in sA:
                if x and value % x == 0 and (y := value // x) in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.mul(ea, eb))
            for x in sA:
                y = x - value
                if y > 0 and y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.sub(ea, eb))
            for x in sA:
                y = x + value
                if y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.sub(eb, ea))
            for y in sB:
                x = value * y
                if x in sA:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.div(ea, eb))
            for x in sA:
                y = value * x
                if y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.div(eb, ea))
        return frozenset(exprs)

    return set(build_exprs(full, cible))
