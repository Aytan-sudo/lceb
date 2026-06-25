"""Modèle 6 — Deux phases, reconstruction cartésienne (origine : main6.py).

Phase 1 : ``reachable(mask)`` = ensemble des valeurs atteignables par le
sous-ensemble, mémoïsé. Sert de pruning (sortie immédiate si la cible est
hors d'atteinte).

Phase 2 : ``build_exprs(mask, value)`` reconstruit les expressions menant à
``value`` en parcourant **tout** le produit (x, y) des valeurs atteignables
des deux moitiés, puis en filtrant celles qui produisent ``value``.
"""

from functools import lru_cache

from . import _render as R
from ._masks import partitions_by_mask

NAME = "twophase_cartesian"
ORIGIN = "main6.py"
DESCRIPTION = "Deux phases : reachability mémoïsée + reconstruction par produit cartésien."


def solve(nombres, cible):
    n = len(nombres)
    full = (1 << n) - 1
    parts = partitions_by_mask(n)

    @lru_cache(maxsize=None)
    def reachable(mask):
        if not (mask & (mask - 1)):
            return frozenset((nombres[mask.bit_length() - 1],))
        vals = set()
        for A, B in parts[mask]:
            for x in reachable(A):
                for y in reachable(B):
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
        return frozenset(vals)

    if cible not in reachable(full):
        return set()

    @lru_cache(maxsize=None)
    def build_exprs(mask, value):
        if not (mask & (mask - 1)):
            v = nombres[mask.bit_length() - 1]
            return frozenset((R.feuille(v),)) if v == value else frozenset()

        exprs = set()
        for A, B in parts[mask]:
            for x in reachable(A):
                for y in reachable(B):
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
                    if y > x and y - x == value:
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
        return frozenset(exprs)

    return set(build_exprs(full, cible))
