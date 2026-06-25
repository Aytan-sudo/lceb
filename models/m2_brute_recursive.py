"""Modèle 2 — Force brute récursive (origine : main2.py).

Même esprit que le modèle 1 : récursion sur l'état, fusion deux à deux,
comptage uniquement quand toutes les plaques sont consommées. La différence
historique avec main1 (comptage des sous-ensembles, élagage des ×1/÷1) a
disparu une fois les deux ramenés à la sémantique « toutes les plaques »,
si bien que les deux modèles produisent désormais le même ensemble : ils
restent distincts pour comparer leurs micro-variations d'exploration.
"""

from . import _render as R

NAME = "brute_recursive"
ORIGIN = "main2.py"
DESCRIPTION = "Force brute récursive, comptage à une seule plaque restante."


def solve(nombres, cible):
    solutions = set()

    def chercher(etat):
        if len(etat) == 1:
            val, expr = etat[0]
            if val == cible:
                solutions.add(expr)
            return

        for i in range(len(etat)):
            for j in range(i + 1, len(etat)):
                v1, e1 = etat[i]
                v2, e2 = etat[j]
                reste = [etat[k] for k in range(len(etat)) if k != i and k != j]

                # Opérandes traités symétriquement (cf. m1_brute_state) pour
                # capturer les deux sens de division à valeurs égales.
                ops = [(v1 + v2, R.add(e1, e2)), (v1 * v2, R.mul(e1, e2))]
                if v1 > v2:
                    ops.append((v1 - v2, R.sub(e1, e2)))
                elif v2 > v1:
                    ops.append((v2 - v1, R.sub(e2, e1)))
                if v2 != 0 and v1 % v2 == 0:
                    ops.append((v1 // v2, R.div(e1, e2)))
                if v1 != 0 and v2 % v1 == 0:
                    ops.append((v2 // v1, R.div(e2, e1)))

                for nv, nexpr in ops:
                    if nv > 0:
                        chercher(reste + [(nv, nexpr)])

    chercher([(n, R.feuille(n)) for n in nombres])
    return solutions
