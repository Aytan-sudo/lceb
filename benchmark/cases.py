"""Cas d'entrée partagés par le benchmark et les tests.

Chaque cas est (plaques, cible). Contrairement à l'ancien benchmark — où
chaque script avait son propre tirage codé en dur — ici **tous les modèles
sont évalués sur les mêmes entrées**, ce qui rend la comparaison honnête.
"""

CASES = [
    ([5, 75, 2, 50, 100, 10], 868),
    ([1, 3, 8, 75, 50, 4], 990),
    ([10, 75, 100, 5, 8, 3], 660),
    ([100, 9, 7, 1], 50),
    ([2, 4, 6, 8, 10, 12], 723),     # souvent sans solution → teste le pruning
]

# Cas lourd (7 plaques) réservé au benchmark « extrême », trop long pour les
# modèles force brute non mémoïsés.
HEAVY = [
    ([25, 50, 75, 100, 3, 6, 7], 952),
]
