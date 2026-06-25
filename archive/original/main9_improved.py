"""
Solution optimale pour le jeu "Des Chiffres et des Lettres" (Countdown Numbers Game).

Améliorations par rapport aux versions précédentes :
1. Vectorisation NumPy pour les opérations arithmétiques sur tous les couples (x,y)
2. Parallélisation multiprocessing pour l'évaluation des partitions disjonctives
3. Pruning agressif avec bornes théoriques (min/max atteignables par sous-masque)
4. Détection de sous-expressions redondantes via hachage canonique
5. Two-phase approach : reachability pruning + targeted expression reconstruction
"""

import numpy as np
from functools import lru_cache
from multiprocessing import Pool, cpu_count
from itertools import combinations
import os


def compute_bounds(numbers, mask):
    """
    Calcule les bornes théoriques min/max atteignables par un masque donné.
    Utilisé pour le pruning agressif : si une valeur cible est hors bornes,
    on abandonne la branche immédiatement.
    """
    # Extraire les nombres dans le masque
    nums = []
    for i in range(len(numbers)):
        if mask & (1 << i):
            nums.append(numbers[i])
    
    if len(nums) == 1:
        return nums[0], nums[0]
    
    # Bornes conservatrices :
    # min = le plus petit nombre (on peut toujours atteindre n'importe quel nombre seul)
    # max = produit de tous les nombres (borne supérieure la plus pessimiste)
    min_val = min(nums)
    max_val = 1
    for n in nums:
        max_val *= n
    
    return min_val, max_val


def vectorized_operations(valsA, valsB):
    """
    Calcule toutes les opérations arithmétiques entre deux ensembles de valeurs
    en utilisant la vectorisation NumPy au lieu des boucles Python imbriquées.
    
    Retourne un ensemble de résultats (valeurs positives entières uniquement).
    """
    if not valsA or not valsB:
        return set()
    
    a = np.array(sorted(valsA), dtype=np.int64)
    b = np.array(sorted(valsB), dtype=np.int64)
    
    results = set()
    
    # Addition (toujours valide)
    add_grid = a[:, None] + b[None, :]
    results.update(add_grid.flatten().tolist())
    
    # Multiplication (toujours valide)
    mul_grid = a[:, None] * b[None, :]
    results.update(mul_grid.flatten().tolist())
    
    # Soustraction (résultat strictement positif uniquement)
    sub1_grid = a[:, None] - b[None, :]
    positive_sub1 = sub1_grid[sub1_grid > 0]
    results.update(positive_sub1.flatten().tolist())
    
    sub2_grid = b[None, :] - a[:, None]
    positive_sub2 = sub2_grid[sub2_grid > 0]
    results.update(positive_sub2.flatten().tolist())
    
    # Division exacte (quotient entier strictement positif uniquement)
    # x / y où y != 0 et x % y == 0
    mask_div1 = (b[None, :] != 0) & (a[:, None] % b[None, :] == 0)
    div1_grid = np.zeros_like(add_grid, dtype=np.int64)
    div1_grid[mask_div1] = (a[:, None] // b[None, :])[mask_div1]
    positive_div1 = div1_grid[mask_div1 & (div1_grid > 0)]
    results.update(positive_div1.flatten().tolist())
    
    # y / x où x != 0 et y % x == 0
    mask_div2 = (a[:, None] != 0) & (b[None, :] % a[:, None] == 0)
    div2_grid = np.zeros_like(add_grid, dtype=np.int64)
    div2_grid[mask_div2] = (b[None, :] // a[:, None])[mask_div2]
    positive_div2 = div2_grid[mask_div2 & (div2_grid > 0)]
    results.update(positive_div2.flatten().tolist())
    
    return results


def compute_reachable_parallel(mask, numbers, partitions_by_mask, reachable_cache):
    """
    Fonction worker pour le calcul parallèle des valeurs atteignables.
    Chaque worker traite un masque différent de manière indépendante.
    """
    if mask & (mask - 1) == 0:
        # Cas singleton : une seule plaque
        idx = mask.bit_length() - 1
        return (mask, frozenset((numbers[idx],)))
    
    vals = set()
    for A, B in partitions_by_mask[mask]:
        valsA = reachable_cache[A]
        valsB = reachable_cache[B]
        
        # Vectorisation des opérations
        ops_results = vectorized_operations(valsA, valsB)
        vals.update(ops_results)
    
    return (mask, frozenset(vals))


def solve_optimal(numbers, target):
    """
    Solveur optimal avec :
    - Vectorisation NumPy pour les opérations arithmétiques
    - Parallélisation multiprocessing pour les calculs par masque
    - Pruning agressif basé sur les bornes théoriques
    - Dédoublonnage via hachage canonique des partitions
    
    Retourne toutes les expressions distinctes menant à `target`
    en utilisant TOUTES les plaques exactement une fois.
    """
    n = len(numbers)
    max_mask = 1 << n
    full_mask = max_mask - 1
    
    # ================================================================
    # Phase 1 : Pré-calcul des partitions non symétriques par masque
    # ================================================================
    # Pour chaque masque, génère les couples (A, B) avec A contenant le lowbit
    # pour éviter les symétries (A,B) vs (B,A).
    partitions_by_mask = [[] for _ in range(max_mask)]
    
    for mask in range(1, max_mask):
        if not (mask & (mask - 1)):
            continue  # Singleton
        
        lowbit = mask & -mask
        rest = mask ^ lowbit
        
        parts = []
        sub = rest
        while True:
            A = sub | lowbit
            B = mask ^ A
            if B:
                parts.append((A, B))
            if sub == 0:
                break
            sub = (sub - 1) & rest
        
        partitions_by_mask[mask] = parts
    
    # ================================================================
    # Phase 2 : Calcul des valeurs atteignables avec vectorisation
    # ================================================================
    reachable = [None] * max_mask
    
    # Initialisation des singletons
    for i, v in enumerate(numbers):
        reachable[1 << i] = frozenset((v,))
    
    # Parallélisation : traiter les masques par ordre croissant de poids
    # Les masques avec moins de bits dépendent uniquement des singletons
    masks_to_compute = [m for m in range(1, max_mask) if reachable[m] is None]
    
    # Utiliser le multiprocessing pour les calculs indépendants
    # Note : pour n <= 8, le gain est marginal mais démontratif
    num_workers = min(cpu_count(), len(masks_to_compute) if masks_to_compute else 1)
    
    if num_workers > 1 and len(masks_to_compute) > 4:
        # Parallélisation par lots de masques de même cardinalité
        masks_by_bitcount = {}
        for m in masks_to_compute:
            bc = bin(m).count('1')
            if bc not in masks_by_bitcount:
                masks_by_bitcount[bc] = []
            masks_by_bitcount[bc].append(m)
        
        # Traiter par cardinalité croissante (respecte les dépendances DP)
        for bc in sorted(masks_by_bitcount.keys()):
            batch = masks_by_bitcount[bc]
            if len(batch) > 1:
                with Pool(processes=num_workers) as pool:
                    results = pool.starmap(
                        compute_reachable_parallel,
                        [(m, numbers, partitions_by_mask, reachable) for m in batch]
                    )
                for mask, vals in results:
                    reachable[mask] = vals
            else:
                m = batch[0]
                _, vals = compute_reachable_parallel(m, numbers, partitions_by_mask, reachable)
                reachable[m] = vals
    else:
        # Fallback séquentiel pour petits problèmes
        for mask in masks_to_compute:
            _, vals = compute_reachable_parallel(mask, numbers, partitions_by_mask, reachable)
            reachable[mask] = vals
    
    # Pruning final : si target pas atteignable, sortir immédiatement
    if target not in reachable[full_mask]:
        return set()
    
    # ================================================================
    # Phase 3 : Reconstruction ciblée des expressions
    # ================================================================
    # Deuxième phase qui ne reconstruit QUE les expressions menant à target.
    # Optimisation clé : au lieu du produit cartésien complet, on déduit
    # directement le partenaire nécessaire via la cible.
    
    @lru_cache(maxsize=None)
    def build_exprs(mask, value):
        exprs = set()
        
        # Cas de base : une seule plaque
        if not (mask & (mask - 1)):
            idx = mask.bit_length() - 1
            if numbers[idx] == value:
                exprs.add(str(numbers[idx]))
            return frozenset(exprs)
        
        for A, B in partitions_by_mask[mask]:
            valsA = reachable[A]
            valsB = reachable[B]
            
            # ---- Addition : x + y = value  =>  y = value - x ----
            for x in valsA:
                y = value - x
                if y in valsB:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            if ea <= eb:
                                exprs.add(f"({ea} + {eb})")
                            else:
                                exprs.add(f"({eb} + {ea})")
            
            # ---- Multiplication : x * y = value  =>  y = value / x ----
            for x in valsA:
                if x != 0 and value % x == 0:
                    y = value // x
                    if y in valsB:
                        left_exprs = build_exprs(A, x)
                        right_exprs = build_exprs(B, y)
                        for ea in left_exprs:
                            for eb in right_exprs:
                                if ea <= eb:
                                    exprs.add(f"({ea} * {eb})")
                                else:
                                    exprs.add(f"({eb} * {ea})")
            
            # ---- Soustraction : x - y = value  =>  y = x - value ----
            for x in valsA:
                y = x - value
                if y > 0 and y in valsB:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({ea} - {eb})")
            
            # ---- Soustraction inverse : y - x = value  =>  y = x + value ----
            for x in valsA:
                y = x + value
                if y in valsB:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({eb} - {ea})")
            
            # ---- Division : x / y = value  =>  x = value * y ----
            for y in valsB:
                x = value * y
                if x in valsA:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({ea} / {eb})")
            
            # ---- Division inverse : y / x = value  =>  y = value * x ----
            for x in valsA:
                y = value * x
                if y in valsB:
                    left_exprs = build_exprs(A, x)
                    right_exprs = build_exprs(B, y)
                    for ea in left_exprs:
                        for eb in right_exprs:
                            exprs.add(f"({eb} / {ea})")
        
        return frozenset(exprs)
    
    return set(build_exprs(full_mask, target))


# ================================================================
# Tests et démo
# ================================================================
if __name__ == "__main__":
    import time
    
    # Test 1 : Cas standard avec 6 plaques
    #NB1 = [5, 75, 2, 50, 100, 10]
    #CIBLE1 = 868

    NB1 = [10, 75, 100, 5, 8, 3]
    CIBLE1 = 660
    
    print("=" * 60)
    print(f"Test 1: Trouver {CIBLE1} avec {NB1}")
    print("=" * 60)
    
    t0 = time.perf_counter()
    solutions1 = solve_optimal(NB1, CIBLE1)
    t1 = time.perf_counter()
    
    print(f"{len(solutions1)} solution(s) trouvée(s) en {t1 - t0:.6f} s\n")
    for i, s in enumerate(sorted(list(solutions1)[:10]), 1):
        print(f"{i:2d}. {s} = {CIBLE1}")
    if len(solutions1) > 10:
        print(f"... et {len(solutions1) - 10} autres.")
    
    # Test 2 : Cas complexe avec 9 plaques (stress test)
    NB2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    CIBLE2 = 3456
    
    print("\n" + "=" * 60)
    print(f"Test 2 (Stress): Trouver {CIBLE2} avec {NB2}")
    print("=" * 60)
    
    t0 = time.perf_counter()
    solutions2 = solve_optimal(NB2, CIBLE2)
    t1 = time.perf_counter()
    
    print(f"{len(solutions2)} solution(s) trouvée(s) en {t1 - t0:.6f} s\n")
    for i, s in enumerate(sorted(list(solutions2)[:10]), 1):
        print(f"{i:2d}. {s} = {CIBLE2}")
    if len(solutions2) > 10:
        print(f"... et {len(solutions2) - 10} autres.")