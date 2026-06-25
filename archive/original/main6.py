from functools import lru_cache

NB = [5, 75, 2, 50, 100, 10]
CIBLE = 868



def solve_target_exhaustive(numbers, target):
    """
    Retourne toutes les expressions distinctes menant à `target`
    en utilisant TOUTES les plaques exactement une fois, avec règles strictes :
      - opérations : +, -, *, /
      - résultats intermédiaires strictement positifs
      - divisions exactes uniquement
      - chaque plaque utilisée exactement une fois
      - dédoublonnage partiel des symétries triviales sur + et *
    """

    n = len(numbers)
    full_mask = (1 << n) - 1

    # ------------------------------------------------------------
    # Pré-calcul des partitions non symétriques pour chaque masque
    # ------------------------------------------------------------
    # Pour un masque donné, on le coupe en (A, B) avec :
    # - A et B non vides
    # - A | B = mask
    # - A & B = 0
    # - un pivot fixé dans A pour éviter A|B et B|A
    #
    # Cela évite de recalculer les bipartitions à chaque appel.
    # ------------------------------------------------------------
    partitions_by_mask = {}

    for mask in range(1, full_mask + 1):
        if mask & (mask - 1) == 0:
            partitions_by_mask[mask] = []
            continue

        lsb = mask & -mask  # bit de poids faible, pivot imposé dans A
        rest = mask ^ lsb

        parts = []
        sub = rest
        while True:
            A = sub | lsb
            B = mask ^ A
            if B != 0:
                parts.append((A, B))
            if sub == 0:
                break
            sub = (sub - 1) & rest

        partitions_by_mask[mask] = parts

    # ------------------------------------------------------------
    # Phase 1 : valeurs atteignables par sous-ensemble
    # reachable(mask) -> frozenset[int]
    # ------------------------------------------------------------
    @lru_cache(maxsize=None)
    def reachable(mask):
        # Cas de base : une seule plaque
        if mask & (mask - 1) == 0:
            idx = mask.bit_length() - 1
            return frozenset((numbers[idx],))

        vals = set()

        for A, B in partitions_by_mask[mask]:
            valsA = reachable(A)
            valsB = reachable(B)

            for x in valsA:
                for y in valsB:
                    # + et * commutatifs : pas besoin de doubler
                    vals.add(x + y)
                    vals.add(x * y)

                    # - : uniquement résultat positif
                    if x > y:
                        vals.add(x - y)
                    elif y > x:
                        vals.add(y - x)

                    # / : uniquement entier strictement positif
                    if y != 0 and x % y == 0:
                        vals.add(x // y)
                    if x != 0 and y % x == 0:
                        vals.add(y // x)

        return frozenset(vals)

    # Petit raccourci : si la cible n'est pas atteignable, on sort tout de suite
    if target not in reachable(full_mask):
        return set()

    # ------------------------------------------------------------
    # Phase 2 : reconstruction ciblée des expressions
    # build_exprs(mask, value) -> frozenset[str]
    # Ne reconstruit que ce qui mène à `value`.
    # ------------------------------------------------------------
    @lru_cache(maxsize=None)
    def build_exprs(mask, value):
        exprs = set()

        # Cas de base
        if mask & (mask - 1) == 0:
            idx = mask.bit_length() - 1
            if numbers[idx] == value:
                exprs.add(str(numbers[idx]))
            return frozenset(exprs)

        for A, B in partitions_by_mask[mask]:
            valsA = reachable(A)
            valsB = reachable(B)

            # On ne parcourt que les couples (x, y) capables de produire `value`
            for x in valsA:
                for y in valsB:
                    # Addition
                    if x + y == value:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)

                        for ea in left_exprs:
                            for eb in right_exprs:
                                # ordre canonique pour + afin d'éviter des doublons triviaux
                                if ea <= eb:
                                    exprs.add(f"({ea} + {eb})")
                                else:
                                    exprs.add(f"({eb} + {ea})")

                    # Multiplication
                    if x * y == value:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)

                        for ea in left_exprs:
                            for eb in right_exprs:
                                # ordre canonique pour * afin d'éviter des doublons triviaux
                                if ea <= eb:
                                    exprs.add(f"({ea} * {eb})")
                                else:
                                    exprs.add(f"({eb} * {ea})")

                    # Soustraction
                    if x > y and x - y == value:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)

                        for ea in left_exprs:
                            for eb in right_exprs:
                                exprs.add(f"({ea} - {eb})")

                    if y > x and y - x == value:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)

                        for ea in left_exprs:
                            for eb in right_exprs:
                                exprs.add(f"({eb} - {ea})")

                    # Division
                    if y != 0 and x % y == 0 and x // y == value:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)

                        for ea in left_exprs:
                            for eb in right_exprs:
                                exprs.add(f"({ea} / {eb})")

                    if x != 0 and y % x == 0 and y // x == value:
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
    solutions = solve_target_exhaustive(NB, CIBLE)
    t1 = time.perf_counter()

    print(f"Recherche exhaustive de {CIBLE} avec {NB}")
    print(f"{len(solutions)} solution(s) trouvée(s) en {t1 - t0:.6f} s\n")

    for i, s in enumerate(sorted(list(solutions)[:10]), 1):
        print(f"{i:2d}. {s} = {CIBLE}")
    if len(solutions) > 10:
        print(f"... et {len(solutions) - 10} autres.")