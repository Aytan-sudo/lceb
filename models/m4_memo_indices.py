"""Modèle 4 — Mémoïsation sur ensembles d'index (origine : main4.py).

Les sous-ensembles sont représentés par des ``frozenset`` d'index (et non
de valeurs) pour gérer correctement les plaques en double. La partition se
fait via ``combinations`` autour d'un pivot fixé à gauche, ce qui évite les
bipartitions symétriques. Chaque sous-ensemble renvoie ``valeur -> {exprs}``.
"""

from itertools import combinations

from . import _render as R

NAME = "memo_indices"
ORIGIN = "main4.py"
DESCRIPTION = "Mémoïsation sur frozenset d'index, partition par combinations."


def solve(nombres, cible):
    memo = {}

    def resoudre(indices):
        if indices in memo:
            return memo[indices]

        resultats = {}

        if len(indices) == 1:
            idx = next(iter(indices))
            v = nombres[idx]
            resultats[v] = {R.feuille(v)}
            memo[indices] = resultats
            return resultats

        liste = list(indices)
        pivot, autres = liste[0], liste[1:]

        for r in range(len(autres) + 1):
            for comb in combinations(autres, r):
                gauche = frozenset([pivot] + list(comb))
                droite = indices - gauche
                if not droite:
                    continue

                rg = resoudre(gauche)
                rd = resoudre(droite)

                for vg, eg in rg.items():
                    for vd, ed in rd.items():
                        for e1 in eg:
                            for e2 in ed:
                                resultats.setdefault(vg + vd, set()).add(R.add(e1, e2))
                                resultats.setdefault(vg * vd, set()).add(R.mul(e1, e2))
                                if vg > vd:
                                    resultats.setdefault(vg - vd, set()).add(R.sub(e1, e2))
                                elif vd > vg:
                                    resultats.setdefault(vd - vg, set()).add(R.sub(e2, e1))
                                if vd != 0 and vg % vd == 0:
                                    resultats.setdefault(vg // vd, set()).add(R.div(e1, e2))
                                if vg != 0 and vd % vg == 0:
                                    resultats.setdefault(vd // vg, set()).add(R.div(e2, e1))

        memo[indices] = resultats
        return resultats

    complet = frozenset(range(len(nombres)))
    return set(resoudre(complet).get(cible, set()))
