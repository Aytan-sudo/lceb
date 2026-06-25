"""Benchmark « extrême » : où chaque approche atteint ses limites.

Contrairement à benchmark/bench.py (cas raisonnables), on vise ici les cas durs
— surtout ceux à **explosion de solutions** (petites plaques). Chaque exécution
tourne dans un processus séparé avec **timeout**, car les modèles force brute
explosent ; un dépassement est signalé sans bloquer le reste.

On mesure aussi ``best_first`` (top-5) pour le situer honnêtement face aux
énumérateurs : il évite de matérialiser tout l'ensemble, mais ne « sauve » pas
le passage à l'échelle — la traversée de reachability domine.

Usage :
    uv run python benchmark/bench_extreme.py
    uv run python benchmark/bench_extreme.py --timeout 30
"""

import argparse
import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import models  # noqa: E402
from benchmark.cases import EXTREME  # noqa: E402


def _worker_model(q, name, nb, cible):
    import models
    t = time.perf_counter()
    sols = models.get(name).solve(list(nb), cible)
    q.put((len(sols), time.perf_counter() - t))


def _worker_best(q, nb, cible):
    import best_first
    t = time.perf_counter()
    res = best_first.solve(list(nb), cible, 5, "primaire")
    q.put((len(res), time.perf_counter() - t))


def _run_timed(target, args, timeout):
    """Lance ``target`` dans un process ; retourne (n, secondes) ou None si timeout."""
    q = mp.Queue()
    p = mp.Process(target=target, args=(q, *args))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return None
    return q.get() if not q.empty() else "erreur"


def run(cases, timeout):
    print(f"Benchmark EXTRÊME — timeout {timeout}s par modèle (process isolé).\n")

    for nombres, cible in cases:
        print("─" * 72)
        print(f"  {nombres}  →  {cible}")
        print("─" * 72)
        print(f"  {'solveur':<22} {'temps':>12}   {'#solutions':>11}")

        for name in models.ORDER:
            res = _run_timed(_worker_model, (name, nombres, cible), timeout)
            if res is None:
                print(f"  {name:<22} {'TIMEOUT':>12}   {'(>' + str(timeout) + 's)':>11}")
            elif res == "erreur":
                print(f"  {name:<22} {'ERREUR':>12}")
            else:
                n, dt = res
                print(f"  {name:<22} {dt * 1000:>10.1f}ms   {n:>11}")

        # best_first (top-5)
        res = _run_timed(_worker_best, (nombres, cible), timeout)
        if res is None:
            print(f"  {'best_first (top5)':<22} {'TIMEOUT':>12}")
        else:
            n, dt = res
            print(f"  {'best_first (top5)':<22} {dt * 1000:>10.1f}ms   {'top ' + str(n):>11}")
        print()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark extrême (cas durs, timeout).")
    parser.add_argument("--timeout", type=float, default=20.0,
                        help="timeout par modèle, en secondes (défaut : 20)")
    args = parser.parse_args(argv)
    run(EXTREME, args.timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
