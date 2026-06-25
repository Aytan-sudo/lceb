"""Modèle 3 — DP descendante sur masques, dictionnaire d'expressions
(origine : main3.py).

Pour chaque sous-ensemble (masque binaire), on construit le dictionnaire
complet ``valeur -> {expressions}``. La table est mémoïsée par masque.
Le résultat final lit l'entrée ``cible`` du masque complet.

Contrairement à l'original (qui mutait une globale ``NB`` + ``lru_cache``),
la mémoïsation est ici locale à l'appel : pas d'effet de bord.
"""

from . import _render as R

NAME = "dp_mask_exprs"
ORIGIN = "main3.py"
DESCRIPTION = "DP descendante par masque, dictionnaire valeur→expressions complet."


def _lowbit_index(mask):
    return (mask & -mask).bit_length() - 1


def _iter_submasks(mask):
    sub = (mask - 1) & mask
    while sub:
        yield sub
        sub = (sub - 1) & mask


def solve(nombres, cible):
    memo = {}

    def build(mask):
        if mask in memo:
            return memo[mask]

        results = {}

        if mask & (mask - 1) == 0:  # singleton
            v = nombres[_lowbit_index(mask)]
            results[v] = {R.feuille(v)}
            memo[mask] = results
            return results

        for A in _iter_submasks(mask):
            B = mask ^ A
            if A >= B:
                continue
            left = build(A)
            right = build(B)
            for v1, exprs1 in left.items():
                for v2, exprs2 in right.items():
                    for e1 in exprs1:
                        for e2 in exprs2:
                            results.setdefault(v1 + v2, set()).add(R.add(e1, e2))
                            results.setdefault(v1 * v2, set()).add(R.mul(e1, e2))
                            if v1 > v2:
                                results.setdefault(v1 - v2, set()).add(R.sub(e1, e2))
                            elif v2 > v1:
                                results.setdefault(v2 - v1, set()).add(R.sub(e2, e1))
                            if v2 != 0 and v1 % v2 == 0:
                                results.setdefault(v1 // v2, set()).add(R.div(e1, e2))
                            if v1 != 0 and v2 % v1 == 0:
                                results.setdefault(v2 // v1, set()).add(R.div(e2, e1))

        memo[mask] = results
        return results

    full = (1 << len(nombres)) - 1
    return set(build(full).get(cible, set()))
