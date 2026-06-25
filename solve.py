"""Point d'entrée unique de la résolution de « Le compte est bon ».

Usage en bibliothèque :

    from solve import solve
    solutions = solve("twophase_targeted", [5, 75, 2, 50, 100, 10], 868)

Usage en ligne de commande :

    uv run python solve.py --nb 5 75 2 50 100 10 --cible 868          # énumère tout
    uv run python solve.py --nb 1 2 3 4 5 6 7 --cible 100 --mode best # top-K direct
    uv run python solve.py --nb 100 25 7 3 --cible 813 --mode closest # le plus proche
    uv run python solve.py --list                                     # liste des modèles

Sémantique : toutes les plaques utilisées exactement une fois (cf. models/).

Modes (--mode) :
  all     énumère toutes les solutions avec --model, en affiche les --top plus lisibles.
  best    reconstruction k-best : top-K direct, mémoire bornée (best_first.py).
  closest si la cible exacte est impossible, vise la valeur atteignable la plus
          proche (closest.py).
"""

import argparse
import sys
import time

import best_first
import closest
import models
import readability


def solve(model, nombres, cible):
    """Résout avec le modèle nommé (énumération exhaustive).

    Retourne un set d'expressions (chaînes). Pour le top-K direct, voir
    ``best_first.solve`` ; pour le plus proche, ``closest.solve``.
    """
    return models.get(model).solve(list(nombres), cible)


# ──────────────────────────── Rendu CLI ────────────────────────────

def _bloc_solutions(meilleures, valeur, level):
    """Lignes des solutions (titre + chaque solution compacte + pas-à-pas)."""
    if not meilleures:
        return ["  Aucune solution."]
    titre = "La plus simple :" if len(meilleures) == 1 else f"Les {len(meilleures)} plus simples :"
    lignes = [f"  {titre}", ""]
    for i, s in enumerate(meilleures, 1):
        lignes.append(readability.format_solution(s, valeur, numero=i))
        lignes.append("")
    return lignes


def _entete(titre, nombres, cible, secondes, statut):
    return [
        "═" * 64,
        f"  Le compte est bon — {titre}",
        "═" * 64,
        f"  Plaques : {nombres}",
        f"  Cible   : {cible}",
        f"  Temps   : {secondes * 1000:.2f} ms",
        statut,
        "─" * 64,
    ]


def rapport_all(model, nombres, cible, secondes, solutions, top, level):
    mod = models.get(model)
    statut = f"  Solutions : {len(solutions)}   (niveau : {level})"
    lignes = _entete(f"modèle « {mod.NAME} » (ex-{mod.ORIGIN})", nombres, cible, secondes, statut)
    if not solutions:
        lignes.append("  Aucune solution exacte (toutes les plaques).")
        return "\n".join(lignes)
    meilleures = readability.top(solutions, top, level)
    lignes += _bloc_solutions(meilleures, cible, level)
    if len(solutions) > len(meilleures):
        lignes.append(f"  … et {len(solutions) - len(meilleures)} autre(s) solution(s).")
    return "\n".join(lignes).rstrip()


def rapport_best(nombres, cible, secondes, meilleures, top, level):
    statut = f"  Recherche best-first   (niveau : {level}, top {top})"
    lignes = _entete("best-first (top-K direct)", nombres, cible, secondes, statut)
    if not meilleures:
        lignes.append("  Aucune solution exacte (toutes les plaques).")
        return "\n".join(lignes)
    lignes += _bloc_solutions(meilleures, cible, level)
    return "\n".join(lignes).rstrip()


def rapport_closest(nombres, cible, secondes, valeur, ecart, meilleures, level):
    if ecart == 0:
        statut = f"  Cible atteinte exactement   (niveau : {level})"
    else:
        statut = f"  Cible exacte impossible → le plus proche : {valeur} (écart {ecart:+d})"
    lignes = _entete("le plus proche", nombres, cible, secondes, statut)
    lignes += _bloc_solutions(meilleures, valeur, level)
    return "\n".join(lignes).rstrip()


def _print_liste():
    print("Modèles disponibles :\n")
    print(f"  {'nom':<20} {'origine':<22} description")
    print(f"  {'-' * 20} {'-' * 22} {'-' * 30}")
    for nom, origine, desc in models.list_models():
        marque = "  (défaut)" if nom == models.DEFAULT else ""
        print(f"  {nom:<20} {origine:<22} {desc}{marque}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Résolution de « Le compte est bon » (toutes les plaques)."
    )
    parser.add_argument("--mode", choices=("all", "best", "closest"), default="all",
                        help="all : énumère tout ; best : top-K direct ; closest : le plus proche")
    parser.add_argument("--model", "-m", default=models.DEFAULT,
                        help=f"modèle d'énumération pour --mode all (défaut : {models.DEFAULT})")
    parser.add_argument("--nb", "-n", type=int, nargs="+", metavar="PLAQUE",
                        help="les plaques, séparées par des espaces")
    parser.add_argument("--cible", "-c", type=int, help="le résultat à atteindre")
    parser.add_argument("--top", "-t", type=int, default=5,
                        help="nombre de solutions (les plus lisibles) affichées (défaut : 5)")
    parser.add_argument("--lvl", choices=sorted(readability.PROFILES), default=readability.DEFAULT_LEVEL,
                        help=f"niveau scolaire pour le classement (défaut : {readability.DEFAULT_LEVEL})")
    parser.add_argument("--list", action="store_true", help="lister les modèles et sortir")
    args = parser.parse_args(argv)

    if args.list:
        _print_liste()
        return 0

    if args.nb is None or args.cible is None:
        parser.error("--nb et --cible sont requis (ou utilisez --list).")

    if args.mode == "all":
        try:
            models.get(args.model)
        except KeyError as e:
            parser.error(str(e))
        t0 = time.perf_counter()
        solutions = solve(args.model, args.nb, args.cible)
        dt = time.perf_counter() - t0
        print(rapport_all(args.model, args.nb, args.cible, dt, solutions, args.top, args.lvl))

    elif args.mode == "best":
        t0 = time.perf_counter()
        meilleures = best_first.solve(args.nb, args.cible, args.top, args.lvl)
        dt = time.perf_counter() - t0
        print(rapport_best(args.nb, args.cible, dt, meilleures, args.top, args.lvl))

    else:  # closest
        t0 = time.perf_counter()
        valeur, ecart, meilleures = closest.solve(args.nb, args.cible, args.top, args.lvl)
        dt = time.perf_counter() - t0
        print(rapport_closest(args.nb, args.cible, dt, valeur, ecart, meilleures, args.lvl))

    return 0


if __name__ == "__main__":
    sys.exit(main())
