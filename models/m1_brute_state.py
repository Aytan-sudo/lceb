"""Modèle 1 — Force brute sur l'état (origine : main1.py).

Récursion naïve, sans mémoïsation. L'état courant est une liste de couples
(valeur, expression). À chaque étape on fusionne deux éléments par une
opération et on recurse sur le reste. Une solution est comptée uniquement
quand il ne reste qu'un seul élément (→ toutes les plaques utilisées).

Le plus simple et le plus lent : sert de référence pédagogique.
"""

from . import _render as R

NAME = "brute_state"
ORIGIN = "main1.py"
DESCRIPTION = "Force brute récursive sur une liste d'état, sans cache."


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

                # Opérandes traités symétriquement (comme les modèles DP) : on ne
                # trie pas par valeur, afin de ne pas perdre le sens « inverse »
                # d'une division quand les deux opérandes ont la même valeur mais
                # des expressions distinctes (ex. (3+5)/8 ET 8/(3+5), tous deux = 1).
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
