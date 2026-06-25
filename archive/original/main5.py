NB = [1, 3, 8, 75, 50, 4]
CIBLE = 990

def solve_ultrafast(nombres, cible):
    n = len(nombres)
    max_mask = 1 << n
    
    # Un tableau natif pour le cache, indexé directement par les masques
    dp = [{} for _ in range(max_mask)]
    
    # 1. Initialisation des cas de base (masques contenant 1 seule plaque)
    for i in range(n):
        dp[1 << i] = {nombres[i]: {str(nombres[i])}}
        
    # 2. Remplissage itératif (Bottom-Up)
    for mask in range(1, max_mask):
        # Ignorer les puissances de 2 (déjà remplies aux cas de base)
        if not (mask & (mask - 1)):
            continue
            
        res = dp[mask]
        
        # L'astuce du "Low Bit" : on force le sous-masque A à contenir le premier bit.
        # Cela évite de calculer symétriquement (A, B) puis (B, A).
        lb = mask & -mask
        
        # Parcours ultra-rapide des sous-masques (sans générateur "yield")
        sub = (mask - 1) & mask
        while sub:
            if sub & lb:
                left = dp[sub]
                right = dp[mask ^ sub]
                
                for v1, exprs1 in left.items():
                    for v2, exprs2 in right.items():
                        for e1 in exprs1:
                            for e2 in exprs2:
                                # Tri inline pour l'ordre canonique (+ et *)
                                if e1 <= e2:
                                    a, b = e1, e2
                                else:
                                    a, b = e2, e1
                                    
                                # Addition
                                v_add = v1 + v2
                                if v_add not in res: res[v_add] = set()
                                res[v_add].add(f"({a} + {b})")
                                
                                # Multiplication
                                v_mul = v1 * v2
                                if v_mul not in res: res[v_mul] = set()
                                res[v_mul].add(f"({a} * {b})")
                                
                                # Soustraction
                                if v1 > v2:
                                    v_sub = v1 - v2
                                    if v_sub not in res: res[v_sub] = set()
                                    res[v_sub].add(f"({e1} - {e2})")
                                elif v2 > v1:
                                    v_sub = v2 - v1
                                    if v_sub not in res: res[v_sub] = set()
                                    res[v_sub].add(f"({e2} - {e1})")
                                    
                                # Division (évite les divisions par zéro directes)
                                if v2 and not v1 % v2:
                                    v_div = v1 // v2
                                    if v_div not in res: res[v_div] = set()
                                    res[v_div].add(f"({e1} / {e2})")
                                if v1 and not v2 % v1:
                                    v_div = v2 // v1
                                    if v_div not in res: res[v_div] = set()
                                    res[v_div].add(f"({e2} / {e1})")
                                    
            # Itération du sous-masque suivant
            sub = (sub - 1) & mask

    # 3. Récupération de toutes les solutions (incluant les sous-ensembles)
    toutes_solutions = set()
    for mask in range(1, max_mask):
        if cible in dp[mask]:
            toutes_solutions.update(dp[mask][cible])
            
    return toutes_solutions

if __name__ == "__main__":
    solutions = solve_ultrafast(NB, CIBLE)
    if solutions:
        # Affiche seulement les 10 premières pour ne pas polluer le terminal du benchmark
        print(f"{len(solutions)} solution(s) trouvée(s) :")
        for i, sol in enumerate(list(solutions)[:10], 1):
            print(f"Solution {i} : {sol} = {CIBLE}")
        if len(solutions) > 10:
            print(f"... et {len(solutions) - 10} autres.")
    else:
        print("Aucune solution trouvée.")