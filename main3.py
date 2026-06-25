from collections import defaultdict
from functools import lru_cache

# ------------------------------------------------------------
# Paramètres
# ------------------------------------------------------------

NB = [1, 3, 8, 75, 50, 4]
CIBLE = 990

# Règles :
# - chaque plaque utilisée au plus / exactement une fois selon le masque final demandé
# - opérations autorisées : +, -, *, /
# - résultats intermédiaires : entiers strictement positifs
# - divisions exactes uniquement
# - pas de doublons triviaux par commutativité sur + et *
#
# Ici, la fonction finale "solutions_exactes_avec_toutes_les_plaques"
# impose l'usage de toutes les plaques exactement une fois.
#
# Si tu veux aussi les solutions avec sous-ensemble de plaques seulement,
# il y a une fonction dédiée plus bas.


# ------------------------------------------------------------
# Outils
# ------------------------------------------------------------

def bit_count(x: int) -> int:
    return x.bit_count()


def lowbit_index(mask: int) -> int:
    """Renvoie l'index du bit de poids faible."""
    return (mask & -mask).bit_length() - 1


def iter_submasks(mask: int):
    """Itère sur les sous-masques non vides propres de mask."""
    sub = (mask - 1) & mask
    while sub:
        yield sub
        sub = (sub - 1) & mask


def canonical_commutative(e1: str, e2: str):
    """Ordre canonique pour + et * afin d'éviter les doublons triviaux."""
    return (e1, e2) if e1 <= e2 else (e2, e1)


# ------------------------------------------------------------
# DP principale
# ------------------------------------------------------------

@lru_cache(maxsize=None)
def build(mask: int):
    """
    Pour un sous-ensemble 'mask', renvoie un dict:
        valeur atteignable -> set(expressions)
    où chaque expression utilise exactement les plaques de 'mask'.
    """
    results = defaultdict(set)

    # Cas de base : une seule plaque
    if mask & (mask - 1) == 0:
        i = lowbit_index(mask)
        v = NB[i]
        results[v].add(str(v))
        return results

    # Décomposition en deux sous-ensembles disjoints A et B
    # On impose A < B pour ne traiter chaque bipartition qu'une fois.
    for A in iter_submasks(mask):
        B = mask ^ A
        if A >= B:
            continue

        left = build(A)
        right = build(B)

        for v1, exprs1 in left.items():
            for v2, exprs2 in right.items():
                for e1 in exprs1:
                    for e2 in exprs2:
                        # Addition
                        a1, a2 = canonical_commutative(e1, e2)
                        results[v1 + v2].add(f"({a1} + {a2})")

                        # Multiplication
                        a1, a2 = canonical_commutative(e1, e2)
                        results[v1 * v2].add(f"({a1} * {a2})")

                        # Soustraction : on garde seulement les résultats positifs
                        if v1 > v2:
                            results[v1 - v2].add(f"({e1} - {e2})")
                        elif v2 > v1:
                            results[v2 - v1].add(f"({e2} - {e1})")

                        # Division exacte, résultat entier positif
                        if v2 != 0 and v1 % v2 == 0:
                            q = v1 // v2
                            if q > 0:
                                results[q].add(f"({e1} / {e2})")

                        if v1 != 0 and v2 % v1 == 0:
                            q = v2 // v1
                            if q > 0:
                                results[q].add(f"({e2} / {e1})")

    return results


# ------------------------------------------------------------
# API haut niveau
# ------------------------------------------------------------

def solutions_exactes_avec_toutes_les_plaques(nombres, cible):
    """
    Exhaustif avec usage exact de toutes les plaques.
    """
    global NB
    NB = list(nombres)
    build.cache_clear()

    full_mask = (1 << len(NB)) - 1
    table = build(full_mask)
    return table.get(cible, set())


def solutions_avec_sous_ensembles(nombres, cible):
    """
    Exhaustif sur tous les sous-ensembles non vides.
    Une solution peut donc ne pas utiliser toutes les plaques.
    """
    global NB
    NB = list(nombres)
    build.cache_clear()

    all_solutions = set()
    full_mask = (1 << len(NB)) - 1

    for mask in range(1, full_mask + 1):
        table = build(mask)
        all_solutions.update(table.get(cible, set()))

    return all_solutions


# ------------------------------------------------------------
# Démonstration
# ------------------------------------------------------------

if __name__ == "__main__":
    sols = solutions_exactes_avec_toutes_les_plaques(NB, CIBLE)

    print(f"{len(sols)} solution(s) exacte(s) avec toutes les plaques :")
    for i, s in enumerate(sorted(sols), 1):
        print(f"{i:2d}. {s} = {CIBLE}")

    print()

    sols_subset = solutions_avec_sous_ensembles(NB, CIBLE)
    print(f"{len(sols_subset)} solution(s) en autorisant les sous-ensembles :")
    for i, s in enumerate(sorted(sols_subset), 1):
        print(f"{i:2d}. {s} = {CIBLE}")