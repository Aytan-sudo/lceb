from functools import lru_cache
from typing import Set, FrozenSet


NB = [1, 3, 8, 75, 50, 4]
CIBLE = 990


NB = [1, 2, 3, 4, 5, 6, 7, 8, 9]
CIBLE = 3456


def solve_fastest_exhaustive(
    numbers: list[int],
    target: int,
) -> Set[str]:
    """
    Résolution exhaustive du jeu « Des Chiffres et des Lettres » (Countdown Numbers Game).

    Retourne *toutes* les expressions arithmétiques distinctes qui atteignent
    exactement ``target`` en utilisant **chaque** plaque de ``numbers`` une
    fois — et aucune de plus.

    Paramètres
    ----------
    numbers : list[int]
        Collection des plaques numériques disponibles (ex: ``[1, 2, 3, 4, 5, 6]``).
    target : int
        Valeur cible à atteindre.

    Retourne
    --------
    Set[str]
        Ensemble de chaînes représentant les expressions valides.
        Chaque chaîne utilise les opérateurs ``+``, ``-``, ``*``, ``/``
        et des parenthèses explicites. L'ordre canonique est imposé
        pour ``+`` et ``*`` afin de réduire les symétries triviales.

    Règles du jeu
    -------------
    - Opérations autorisées : addition, soustraction, multiplication, division.
    - Résultats intermédiaires strictement positifs (``> 0``).
    - Divisions exactes uniquement (le dividende est un multiple du diviseur).
    - Chaque plaque est utilisée **exactement** une fois.

    Algorithme
    ----------
    Deux phases basées sur la programmation dynamique par masques bit à bit :

    1. **Reachability** — Pour chaque sous-ensemble (représenté par un masque
       binaire), calculer l'ensemble des valeurs entières positives
       atteignables en combinant les plaques de ce sous-ensemble.

    2. **Reconstruction ciblée** — En partant du masque complet et de la
       valeur ``target``, remonter récursivement uniquement les branches
       qui mènent à la cible, en déduisant directement le partenaire
       nécessaire pour chaque opération (ex: pour ``x + y = target``,
       on cherche ``y = target - x`` au lieu du produit cartésien complet).

    Les partitions disjonctives de chaque masque sont pré-calculées une fois
    et stockées dans ``partitions_by_mask``. La symétrie ``(A, B) ↔ (B, A)``
    est évitée en imposant que la partition ``A`` contienne toujours le
    *low bit* du masque.

    Exemple
    -------
    >>> solutions = solve_fastest_exhaustive([50, 2, 1], 100)
    >>> any("100" in s for s in solutions)
    True
    """
    # ------------------------------------------------------------------
    n: int = len(numbers)
    max_mask: int = 1 << n
    full_mask: int = max_mask - 1

    # ------------------------------------------------------------
    # 1) Pré-calcul des partitions non symétriques pour chaque masque
    # ------------------------------------------------------------
    partitions_by_mask: list[list[tuple[int, int]]] = [[] for _ in range(max_mask)]

    for mask in range(1, max_mask):
        if not (mask & (mask - 1)):
            continue  # singleton

        lowbit: int = mask & -mask
        rest: int = mask ^ lowbit

        parts: list[tuple[int, int]] = []
        sub: int = rest
        while True:
            A: int = sub | lowbit
            B: int = mask ^ A
            if B:
                parts.append((A, B))
            if sub == 0:
                break
            sub = (sub - 1) & rest

        partitions_by_mask[mask] = parts

    # ------------------------------------------------------------
    # 2) DP des valeurs atteignables par masque
    # ------------------------------------------------------------
    reachable: list[FrozenSet[int] | None] = [None] * max_mask

    for i, v in enumerate(numbers):
        reachable[1 << i] = frozenset((v,))

    for mask in range(1, max_mask):
        if reachable[mask] is not None:
            continue

        vals: set[int] = set()

        for A, B in partitions_by_mask[mask]:
            valsA: FrozenSet[int] = reachable[A]  # type: ignore[assignment]
            valsB: FrozenSet[int] = reachable[B]  # type: ignore[assignment]

            for x in valsA:
                for y in valsB:
                    vals.add(x + y)
                    vals.add(x * y)
                    if x > y:
                        vals.add(x - y)
                    elif y > x:
                        vals.add(y - x)
                    if y and x % y == 0:
                        q = x // y
                        if q > 0:
                            vals.add(q)
                    if x and y % x == 0:
                        q = y // x
                        if q > 0:
                            vals.add(q)

        reachable[mask] = frozenset(vals)

    if target not in reachable[full_mask]:
        return set()

    # ------------------------------------------------------------
    # 3) Reconstruction ciblée des expressions
    # ------------------------------------------------------------
    @lru_cache(maxsize=None)
    def build_exprs(mask: int, value: int) -> FrozenSet[str]:
        exprs: set[str] = set()

        if not (mask & (mask - 1)):
            idx: int = mask.bit_length() - 1
            if numbers[idx] == value:
                exprs.add(str(numbers[idx]))
            return frozenset(exprs)

        for A, B in partitions_by_mask[mask]:
            valsA = reachable[A]
            valsB = reachable[B]

            valsA_set: FrozenSet[int] = valsA  # type: ignore[assignment]
            valsB_set: FrozenSet[int] = valsB  # type: ignore[assignment]

            # Addition : x + y = value
            for x in valsA:
                y = value - x
                if y in valsB_set:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            if ea <= eb:
                                exprs.add(f"({ea} + {eb})")
                            else:
                                exprs.add(f"({eb} + {ea})")

            # Multiplication : x * y = value
            for x in valsA:
                if x != 0 and value % x == 0:
                    y = value // x
                    if y in valsB_set:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)
                        for ea in left_exprs:
                            for eb in right_exprs:
                                if ea <= eb:
                                    exprs.add(f"({ea} * {eb})")
                                else:
                                    exprs.add(f"({eb} * {ea})")

            # Soustraction : x - y = value
            for x in valsA:
                y = x - value
                if y > 0 and y in valsB_set:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({ea} - {eb})")

            # Soustraction inverse : y - x = value
            for x in valsA:
                y = x + value
                if y in valsB_set:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({eb} - {ea})")

            # Division : x / y = value
            for y in valsB:
                x = value * y
                if x in valsA_set:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({ea} / {eb})")

            # Division inverse : y / x = value
            for x in valsA:
                y = value * x
                if y in valsB_set:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({eb} / {ea})")

        return frozenset(exprs)

    return set(build_exprs(full_mask, target))


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    solutions = solve_fastest_exhaustive(NB, CIBLE)
    t1 = time.perf_counter()

    print(f"Recherche exhaustive de {CIBLE} avec {NB}")
    print(f"{len(solutions)} solution(s) trouvée(s) en {t1 - t0:.6f} s\n")

    for i, s in enumerate(sorted(list(solutions)[:10]), 1):
        print(f"{i:2d}. {s} = {CIBLE}")
    if len(solutions) > 10:
        print(f"... et {len(solutions) - 10} autres.")