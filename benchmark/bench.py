"""Benchmark équitable des modèles de résolution.

Tous les modèles sont exécutés **dans le même processus** sur **les mêmes
entrées** (benchmark/cases.py), chronométrés sur plusieurs itérations.
On vérifie en prime que tous les modèles renvoient le même ensemble de
solutions pour chaque cas (cohérence), et on signale toute divergence.

Usage :
    uv run python benchmark/bench.py            # cas standards
    uv run python benchmark/bench.py --heavy    # ajoute le cas à 7 plaques
    uv run python benchmark/bench.py --iters 10
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import models  # noqa: E402
from benchmark.cases import CASES, HEAVY  # noqa: E402


def _mesure(fn, nombres, cible, iters):
    temps = []
    sols = None
    for _ in range(iters):
        t0 = time.perf_counter()
        res = fn(list(nombres), cible)
        temps.append(time.perf_counter() - t0)
        sols = res
    return sols, temps


def run(cases, iters):
    noms = models.ORDER

    # Référence de cohérence : le modèle par défaut.
    ref_mod = models.get(models.DEFAULT)

    print(f"Benchmark sur {len(cases)} cas × {iters} itérations "
          f"(processus unique, mêmes entrées).\n")

    # Totaux cumulés par modèle (somme des temps médians sur tous les cas).
    cumul = {n: 0.0 for n in noms}
    divergences = []

    for nombres, cible in cases:
        ref_sols = ref_mod.solve(list(nombres), cible)
        print("─" * 72)
        print(f"  {nombres}  →  {cible}   ({len(ref_sols)} solutions)")
        print("─" * 72)
        print(f"  {'modèle':<20} {'médian':>11} {'min':>11} {'max':>11}   cohérence")

        for nom in noms:
            mod = models.get(nom)
            sols, temps = _mesure(mod.solve, nombres, cible, iters)
            med = statistics.median(temps)
            cumul[nom] += med

            if sols == ref_sols:
                coherence = "✓"
            else:
                coherence = f"✗ ({len(sols)} sol)"
                divergences.append((nom, nombres, cible, sols, ref_sols))

            print(f"  {nom:<20} {med * 1000:>9.2f}ms {min(temps) * 1000:>9.2f}ms "
                  f"{max(temps) * 1000:>9.2f}ms   {coherence}")
        print()

    # Classement global.
    print("═" * 72)
    print("  Classement global (somme des temps médians sur tous les cas)")
    print("═" * 72)
    classement = sorted(noms, key=lambda n: cumul[n])
    for rang, nom in enumerate(classement, 1):
        print(f"  {rang}. {nom:<20} {cumul[nom] * 1000:>9.2f} ms")

    if divergences:
        print("\n⚠️  DIVERGENCES détectées :")
        for nom, nombres, cible, sols, ref in divergences:
            only_mod = sorted(sols - ref)[:3]
            only_ref = sorted(ref - sols)[:3]
            print(f"  {nom} sur {nombres}→{cible} : "
                  f"+{len(sols - ref)} -{len(ref - sols)}  "
                  f"only_modèle={only_mod} only_ref={only_ref}")
        return 1

    print("\n✓ Tous les modèles concordent sur tous les cas.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark équitable des modèles.")
    parser.add_argument("--iters", "-i", type=int, default=5,
                        help="itérations par modèle et par cas (défaut : 5)")
    parser.add_argument("--heavy", action="store_true",
                        help="ajoute le cas lourd à 7 plaques (lent pour les modèles naïfs)")
    args = parser.parse_args(argv)

    cases = list(CASES) + (list(HEAVY) if args.heavy else [])
    return run(cases, args.iters)


if __name__ == "__main__":
    sys.exit(main())
