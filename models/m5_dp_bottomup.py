"""Modèle 5 — DP ascendante itérative (origine : main5.py).

Remplissage « bottom-up » : on parcourt les masques par valeur croissante,
chaque masque combinant deux sous-masques déjà calculés (astuce du low-bit
pour ne traiter chaque bipartition qu'une fois). Comme l'original collectait
les solutions sur *tous* les masques (sous-ensembles), on restreint ici la
lecture finale au masque complet pour rester en sémantique « toutes plaques ».
"""

from . import _render as R

NAME = "dp_bottomup"
ORIGIN = "main5.py"
DESCRIPTION = "DP ascendante itérative sur masques, dictionnaire valeur→expressions."


def solve(nombres, cible):
    n = len(nombres)
    max_mask = 1 << n
    dp = [{} for _ in range(max_mask)]

    for i in range(n):
        dp[1 << i] = {nombres[i]: {R.feuille(nombres[i])}}

    for mask in range(1, max_mask):
        if not (mask & (mask - 1)):
            continue

        res = dp[mask]
        lb = mask & -mask
        sub = (mask - 1) & mask
        while sub:
            if sub & lb:
                left = dp[sub]
                right = dp[mask ^ sub]
                for v1, exprs1 in left.items():
                    for v2, exprs2 in right.items():
                        for e1 in exprs1:
                            for e2 in exprs2:
                                res.setdefault(v1 + v2, set()).add(R.add(e1, e2))
                                res.setdefault(v1 * v2, set()).add(R.mul(e1, e2))
                                if v1 > v2:
                                    res.setdefault(v1 - v2, set()).add(R.sub(e1, e2))
                                elif v2 > v1:
                                    res.setdefault(v2 - v1, set()).add(R.sub(e2, e1))
                                if v2 and not v1 % v2:
                                    res.setdefault(v1 // v2, set()).add(R.div(e1, e2))
                                if v1 and not v2 % v1:
                                    res.setdefault(v2 // v1, set()).add(R.div(e2, e1))
            sub = (sub - 1) & mask

    full = max_mask - 1
    return set(dp[full].get(cible, set()))
