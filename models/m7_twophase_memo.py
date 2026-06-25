"""Modèle 7 — Deux phases, reachability ascendante (origine : main7.py).

Variante du modèle 6 : la phase 1 remplit ``dp_vals[mask]`` (un set de
valeurs) de façon **ascendante** plutôt que par récursion mémoïsée, et la
phase 2 utilise un dictionnaire de mémoïsation manuel (et non ``lru_cache``).
La reconstruction reste cartésienne.
"""

from . import _render as R
from ._masks import partitions_by_mask

NAME = "twophase_memo"
ORIGIN = "main7.py"
DESCRIPTION = "Deux phases : reachability ascendante + reconstruction (memo manuel)."


def solve(nombres, cible):
    n = len(nombres)
    full = (1 << n) - 1
    parts = partitions_by_mask(n)

    dp_vals = [set() for _ in range(full + 1)]
    for i in range(n):
        dp_vals[1 << i].add(nombres[i])

    for mask in range(1, full + 1):
        if not parts[mask]:
            continue
        res = dp_vals[mask]
        for A, B in parts[mask]:
            for x in dp_vals[A]:
                for y in dp_vals[B]:
                    res.add(x + y)
                    res.add(x * y)
                    if x > y:
                        res.add(x - y)
                    elif y > x:
                        res.add(y - x)
                    if y and x % y == 0:
                        res.add(x // y)
                    if x and y % x == 0:
                        res.add(y // x)

    if cible not in dp_vals[full]:
        return set()

    memo = {}

    def build_exprs(mask, value):
        state = (mask, value)
        if state in memo:
            return memo[state]

        exprs = set()
        if not (mask & (mask - 1)):
            v = nombres[mask.bit_length() - 1]
            if v == value:
                exprs.add(R.feuille(v))
            memo[state] = exprs
            return exprs

        for A, B in parts[mask]:
            for x in dp_vals[A]:
                for y in dp_vals[B]:
                    if x + y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(R.add(ea, eb))
                    if x * y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(R.mul(ea, eb))
                    if x > y and x - y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(R.sub(ea, eb))
                    elif y > x and y - x == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(R.sub(eb, ea))
                    if y and x % y == 0 and x // y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(R.div(ea, eb))
                    if x and y % x == 0 and y // x == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(R.div(eb, ea))

        memo[state] = exprs
        return exprs

    return set(build_exprs(full, cible))
