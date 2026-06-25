"""Point d'entrée unique de la résolution de « Le compte est bon ».

Usage en bibliothèque :

    from solve import solve
    solutions = solve("twophase_targeted", [5, 75, 2, 50, 100, 10], 868)

Usage en ligne de commande :

    uv run python solve.py --model twophase_targeted --nb 5 75 2 50 100 10 --cible 868
    uv run python solve.py --nb 1 3 8 75 50 4 --cible 990        # modèle par défaut
    uv run python solve.py --list                                 # liste des modèles

Sémantique : toutes les plaques utilisées exactement une fois (cf. models/).
"""

import argparse
import sys
import time

import models


def solve(model, nombres, cible):
    """Résout avec le modèle nommé. Retourne un set d'expressions (chaînes).

    model   : nom d'un modèle du registre (cf. models.ORDER)
    nombres : liste des plaques
    cible   : entier à atteindre
    """
    return models.get(model).solve(list(nombres), cible)


# ──────────────────────────── Rendu CLI ────────────────────────────

def format_rapport(model, nombres, cible, solutions, secondes, limite=20):
    """Rendu texte harmonisé d'une résolution."""
    mod = models.get(model)
    lignes = []
    lignes.append("═" * 64)
    lignes.append(f"  Le compte est bon — modèle « {mod.NAME} » (ex-{mod.ORIGIN})")
    lignes.append("═" * 64)
    lignes.append(f"  Plaques : {nombres}")
    lignes.append(f"  Cible   : {cible}")
    lignes.append(f"  Temps   : {secondes * 1000:.2f} ms")
    lignes.append(f"  Solutions : {len(solutions)}")
    lignes.append("─" * 64)

    if not solutions:
        lignes.append("  Aucune solution exacte (toutes les plaques).")
    else:
        for i, s in enumerate(sorted(solutions)[:limite], 1):
            lignes.append(f"  {i:3d}. {s} = {cible}")
        if len(solutions) > limite:
            lignes.append(f"  … et {len(solutions) - limite} autre(s).")

    return "\n".join(lignes)


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
    parser.add_argument("--model", "-m", default=models.DEFAULT,
                        help=f"modèle à utiliser (défaut : {models.DEFAULT})")
    parser.add_argument("--nb", "-n", type=int, nargs="+", metavar="PLAQUE",
                        help="les plaques, séparées par des espaces")
    parser.add_argument("--cible", "-c", type=int, help="le résultat à atteindre")
    parser.add_argument("--limite", "-l", type=int, default=20,
                        help="nombre max de solutions affichées (défaut : 20)")
    parser.add_argument("--list", action="store_true", help="lister les modèles et sortir")
    args = parser.parse_args(argv)

    if args.list:
        _print_liste()
        return 0

    if args.nb is None or args.cible is None:
        parser.error("--nb et --cible sont requis (ou utilisez --list).")

    try:
        models.get(args.model)
    except KeyError as e:
        parser.error(str(e))

    t0 = time.perf_counter()
    solutions = solve(args.model, args.nb, args.cible)
    dt = time.perf_counter() - t0

    print(format_rapport(args.model, args.nb, args.cible, solutions, dt, args.limite))
    return 0


if __name__ == "__main__":
    sys.exit(main())
