"""Modèle 8 — Deux phases, reconstruction *ciblée* (origine : main8.py).

Le modèle le plus rapide en Python pur. La phase 2 ne fait pas de produit
cartésien : pour chaque opération, elle **déduit** directement le partenaire
nécessaire à partir de la cible (ex. pour ``x + y = value``, on cherche
``y = value - x`` ; pour ``x * y = value``, ``y = value / x`` ; etc.) et
vérifie son appartenance à l'ensemble atteignable de l'autre moitié.
"""

from functools import lru_cache

from . import _render as R
from ._masks import partitions_by_mask

NAME = "twophase_targeted"
ORIGIN = "main8.py"
DESCRIPTION = "Deux phases : reachability + reconstruction ciblée (déduction du partenaire)."


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
            for x in reachable[A]:
                for y in reachable[B]:
                    vals.add(x + y)
                    vals.add(x * y)
                    if x > y:
                        vals.add(x - y)
                    elif y > x:
                        vals.add(y - x)
                    if y and x % y == 0:
                        vals.add(x // y)
                    if x and y % x == 0:
                        vals.add(y // x)
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

            # Addition : x + y = value
            for x in sA:
                y = value - x
                if y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.add(ea, eb))
            # Multiplication : x * y = value
            for x in sA:
                if x and value % x == 0 and (y := value // x) in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.mul(ea, eb))
            # Soustraction : x - y = value
            for x in sA:
                y = x - value
                if y > 0 and y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.sub(ea, eb))
            # Soustraction inverse : y - x = value
            for x in sA:
                y = x + value
                if y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.sub(eb, ea))
            # Division : x / y = value
            for y in sB:
                x = value * y
                if x in sA:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.div(ea, eb))
            # Division inverse : y / x = value
            for x in sA:
                y = value * x
                if y in sB:
                    for ea in build_exprs(A, x):
                        for eb in build_exprs(B, y):
                            exprs.add(R.div(eb, ea))
        return frozenset(exprs)

    return set(build_exprs(full, cible))
