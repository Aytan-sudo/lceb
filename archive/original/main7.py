

NB = [10, 75, 100, 5, 8, 3]
CIBLE = 660

def solve_ultimate(nombres, cible):
    n = len(nombres)
    full_mask = (1 << n) - 1

    partitions = [[] for _ in range(full_mask + 1)]
    for mask in range(1, full_mask + 1):
        if not (mask & (mask - 1)):
            continue

        lsb = mask & -mask
        rest = mask ^ lsb
        sub = rest
        while True:
            A = sub | lsb
            B = mask ^ A
            if B:
                partitions[mask].append((A, B))
            if sub == 0:
                break
            sub = (sub - 1) & rest

    dp_vals = [set() for _ in range(full_mask + 1)]
    for i in range(n):
        dp_vals[1 << i].add(nombres[i])

    for mask in range(1, full_mask + 1):
        if not partitions[mask]:
            continue

        res = dp_vals[mask]
        for A, B in partitions[mask]:
            for x in dp_vals[A]:
                for y in dp_vals[B]:
                    res.add(x + y)
                    res.add(x * y)
                    if x > y:
                        res.add(x - y)
                    elif y > x:
                        res.add(y - x)
                    if y and x % y == 0:
                        res.add(x // y)
                    if x and y % x == 0:
                        res.add(y // x)

    if cible not in dp_vals[full_mask]:
        return set()

    memo_exprs = {}

    def build_exprs(mask, value):
        state = (mask, value)
        if state in memo_exprs:
            return memo_exprs[state]

        exprs = set()

        if not (mask & (mask - 1)):
            idx = mask.bit_length() - 1
            if nombres[idx] == value:
                exprs.add(str(value))
            memo_exprs[state] = exprs
            return exprs

        for A, B in partitions[mask]:
            for x in dp_vals[A]:
                for y in dp_vals[B]:
                    if x + y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(f"({ea} + {eb})" if ea <= eb else f"({eb} + {ea})")

                    if x * y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(f"({ea} * {eb})" if ea <= eb else f"({eb} * {ea})")

                    if x > y and x - y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(f"({ea} - {eb})")
                    elif y > x and y - x == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(f"({eb} - {ea})")

                    if y and x % y == 0 and x // y == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(f"({ea} / {eb})")
                    if x and y % x == 0 and y // x == value:
                        for ea in build_exprs(A, x):
                            for eb in build_exprs(B, y):
                                exprs.add(f"({eb} / {ea})")

        memo_exprs[state] = exprs
        return exprs

    return build_exprs(full_mask, cible)

# --- Zone de test ---
if __name__ == "__main__":
    import time
    
    t0 = time.perf_counter()
    solutions = solve_ultimate(NB, CIBLE)
    t1 = time.perf_counter()
    
    print(f"Recherche exhaustive de {CIBLE} avec {NB} (Algorithme Ultime)")
    print(f"{len(solutions)} solution(s) exacte(s) trouvée(s) en {t1 - t0:.6f} s\n")
    
    for i, s in enumerate(sorted(list(solutions)[:10]), 1):
        print(f"{i:2d}. {s} = {CIBLE}")
    if len(solutions) > 10:
        print(f"... et {len(solutions) - 10} autres.")