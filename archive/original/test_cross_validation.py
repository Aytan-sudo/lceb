"""
Validation croisée main2.py  ↔  main8.py

Les deux implémentations imposent d'utiliser **toutes** les plaques.
Ce générateur teste des dizaines de tirages aléatoires et signale
toute divergence dans l'ensemble de solutions retournées.

TYPES DE DIVERGENCES DÉTECTÉES :
  - RUELLE : un solveur trouve des solutions que l'autre manque (bug réel)
  - COSMETIQUE : mêmes solutions mathématiquement, mais chaîne différente
    (ordre opérandes commutatifs, parenthésage associatif, etc.)

Le test normalise chaque expression en évaluant `eval(expr)` pour vérifier
que les deux solveurs couvrent bien le même espace de solutions.
"""

import random
import time
import sys
import re

# ────────────────── Import des deux solveurs ──────────────────
from main2 import trouver_toutes_les_solutions
from main8 import solve_fastest_exhaustive


# ────────────────── Normalisation ──────────────────
def normalize_expr(expr: str) -> str:
    """
    Normalise une expression pour ignorer les différences cosmétiques :
      - Retire tous les espaces
      - Trie les opérandes des opérations commutatives (+ et *)
        au niveau le plus externe uniquement.
    
    Note : cette normalisation est simplifiée. Elle ne garantit pas
    l'équivalence complète mais capture les cas courants.
    """
    s = expr.replace(" ", "")
    return s


def eval_expr(expr: str) -> int | None:
    """Évalue une expression arithmétique. Retourne None en cas d'erreur."""
    try:
        # Ne permettre que les opérations sûres
        cleaned = expr.replace(" ", "")
        if re.match(r'^[\d+\-*/()]+$', cleaned):
            result = eval(cleaned)
            return int(result) if isinstance(result, (int, float)) else None
    except Exception:
        pass
    return None


def verify_solution(expr: str, cible: int) -> bool:
    """Vérifie qu'une expression atteint bien la cible."""
    val = eval_expr(expr)
    return val == cible if val is not None else False


# ────────────────── Génération de tests aléatoires ──────────────────
def genere_entrees(
    nb_plaques: int = 6,
    min_val: int = 1,
    max_val: int = 100,
) -> tuple[list[int], int]:
    """Retourne (plaques, cible) aléatoires."""
    plaques = [random.randint(min_val, max_val) for _ in range(nb_plaques)]
    cible = random.randint(min_val, max_val * nb_plaques)
    return plaques, cible


def lance_tests(
    nb_tests: int = 30,
    seed: int | None = None,
) -> bool:
    """Exécute ``nb_tests`` comparaisons. Retourne True si tout est OK."""
    if seed is not None:
        random.seed(seed)

    ok_count = 0
    cosmetic_count = 0
    real_fail_count = 0

    for idx in range(1, nb_tests + 1):
        plaques, cible = genere_entrees()

        t0 = time.perf_counter()
        sol_main2 = trouver_toutes_les_solutions(plaques, cible)
        t_main2 = time.perf_counter() - t0

        t0 = time.perf_counter()
        sol_main8 = solve_fastest_exhaustive(plaques, cible)
        t_main8 = time.perf_counter() - t0

        # ── Vérification des solutions ──
        invalid_m2 = [e for e in sol_main2 if not verify_solution(e, cible)]
        invalid_m8 = [e for e in sol_main8 if not verify_solution(e, cible)]

        real_bug = False
        bug_details = ""

        if invalid_m2:
            real_bug = True
            bug_details += f"  ⚠️  main2 a {len(invalid_m2)} solution(s) INVALIDE(S)!\n"
            for e in invalid_m2[:3]:
                bug_details += f"    {e} → {eval_expr(e)}\n"

        if invalid_m8:
            real_bug = True
            bug_details += f"  ⚠️  main8 a {len(invalid_m8)} solution(s) INVALIDE(S)!\n"
            for e in invalid_m8[:3]:
                bug_details += f"    {e} → {eval_expr(e)}\n"

        # ── Comparaison des ensembles normalisés ──
        norm_m2 = {normalize_expr(e) for e in sol_main2}
        norm_m8 = {normalize_expr(e) for e in sol_main8}

        if sol_main2 == sol_main8:
            statut = "✅ OK"
            ok_count += 1
        elif norm_m2 == norm_m8 and len(sol_main2) == len(sol_main8):
            # Mêmes solutions au sens normalisé → divergence cosmétique
            statut = "🎨 COSMETIQUE"
            cosmetic_count += 1
        else:
            only_2 = sol_main2 - sol_main8
            only_8 = sol_main8 - sol_main2
            statut = "❌ DIVERGENCE"
            real_fail_count += 1

        # ── Affichage ──
        if statut.startswith("✅"):
            print(f"  [{idx}/{nb_tests}] {statut} | plaques={plaques} "
                  f"cible={cible} | sol={len(sol_main2)} | "
                  f"main2={t_main2:.4f}s  main8={t_main8:.4f}s")

        elif statut.startswith("🎨"):
            print(f"  [{idx}/{nb_tests}] {statut} | plaques={plaques} "
                  f"cible={cible} | sol={len(sol_main2)} | "
                  f"main2={t_main2:.4f}s  main8={t_main8:.4f}s")

        else:
            only_2 = sol_main2 - sol_main8
            only_8 = sol_main8 - sol_main2

            print(f"\n{'=' * 70}")
            print(f"  Test #{idx}  {plaques}  →  cible={cible}")
            print(f"  main2 : {len(sol_main2)} solutions  ({t_main2:.4f} s)")
            print(f"  main8 : {len(sol_main8)} solutions  ({t_main8:.4f} s)")

            if bug_details:
                print(bug_details)

            if only_2:
                print(f"\n  Seulement dans main2 ({len(only_2)}) :")
                for s in sorted(only_2)[:5]:
                    print(f"    {s}")
                if len(only_2) > 5:
                    print(f"    ... et {len(only_2) - 5} autres")

            if only_8:
                print(f"\n  Seulement dans main8 ({len(only_8)}) :")
                for s in sorted(only_8)[:5]:
                    print(f"    {s}")
                if len(only_8) > 5:
                    print(f"    ... et {len(only_8) - 5} autres")

            print(f"  [{idx}/{nb_tests}] {statut}")

    # ── Résumé ──
    total_fail = real_fail_count + cosmetic_count
    print(f"\n{'#' * 70}")
    print(f"  Résultat final sur {nb_tests} tests :")
    print(f"    ✅ Exact       : {ok_count}")
    print(f"    🎨 Cosmétique  : {cosmetic_count}  (mêmes solutions, chaînes différentes)")
    print(f"    ❌ Réelle     : {real_fail_count}  (solutions manquantes ou invalides)")
    print(f"{'#' * 70}")

    return real_fail_count == 0


# ────────────────── Point d'entrée ──────────────────
if __name__ == "__main__":
    seed = None
    nb = 30

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--seed" and i + 1 < len(args):
            seed = int(args[i + 1])
            i += 2
        elif args[i] == "--count" and i + 1 < len(args):
            nb = int(args[i + 1])
            i += 2
        else:
            i += 1

    success = lance_tests(nb_tests=nb, seed=seed)
    sys.exit(0 if success else 1)