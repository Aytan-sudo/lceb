"""Solveur « le plus proche » : la vraie règle du jeu télévisé.

Si la cible exacte n'est pas atteignable avec toutes les plaques, on renvoie la
**valeur atteignable la plus proche** (et ses solutions les plus lisibles).
C'est fréquent en devoir : la cible n'est pas toujours faisable.

Réutilise la reachability et la reconstruction k-best de ``best_first``.
"""

import best_first as BF
import readability as R
from models._masks import partitions_by_mask


def solve(numbers, target, k=5, level=R.DEFAULT_LEVEL):
    """Retourne ``(valeur_atteinte, ecart, expressions)``.

    - ``valeur_atteinte`` : ``target`` si atteignable, sinon la valeur
      atteignable la plus proche ;
    - ``ecart`` : ``valeur_atteinte - target`` (0 si exact) ;
    - ``expressions`` : top-``k`` solutions lisibles pour cette valeur.
    """
    n = len(numbers)
    max_mask = 1 << n
    parts = partitions_by_mask(n)
    atteignables = BF._reachable(numbers, parts, max_mask)[max_mask - 1]

    if target in atteignables:
        valeur = target
    else:
        # plus proche ; en cas d'égalité de distance, on prend la plus petite.
        valeur = min(atteignables, key=lambda v: (abs(v - target), v))

    exprs = BF.top_k_for(numbers, valeur, k, level)
    return valeur, valeur - target, exprs
