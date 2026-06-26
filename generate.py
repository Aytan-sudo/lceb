"""Générateur de tirages « Le compte est bon » à difficulté graduée.

Produit des couples (plaques, cible) étiquetés par un **niveau de difficulté**
(`facile` → `expert`). Tout repose sur la réutilisation des briques existantes :

  - tirage de la cible dans l'ensemble *atteignable* (``best_first._reachable``,
    peu coûteux) → une **solution exacte est garantie** par construction ;
  - notation de la difficulté par **multi-signaux** :
      1. la **rareté** des solutions (peu de chemins ⇒ plus dur à trouver) —
         comptée via l'énumération exhaustive d'un modèle de ``models/`` ;
      2. la **dureté de la solution la plus simple** : nombre de ``÷`` puis de
         ``×`` qu'elle impose (jugée par ``readability``, comme pour le
         classement enfant).
    Ces signaux sont combinés en un **indice continu** (plus haut = plus dur),
    puis seuillé en niveau nommé.

Sémantique identique au reste du projet : **toutes les plaques** sont utilisées
exactement une fois.

Indice et seuils sont des **heuristiques réglables** (voir les constantes en
tête de module), dans le même esprit que les ``PROFILES`` de ``readability``.

Utilisation en bibliothèque ::

    from generate import generer, evaluer
    t = generer("difficile", seed=42)
    print(t.plaques, t.cible, t.niveau)

En ligne de commande ::

    uv run python generate.py --niveau facile
    uv run python generate.py --serie                 # un tirage par niveau
    uv run python generate.py --niveau expert --seed 7
"""

import argparse
import math
import random
import sys
from dataclasses import dataclass, field

import models
import readability as R
from best_first import _reachable
from models._masks import partitions_by_mask

# ─────────────────────────── Deck & cibles ───────────────────────────
#
# Deck officiel du jeu télévisé : les petites plaques 1..10 en double, les
# grosses 25/50/75/100 en simple. ``rng.sample`` tire des positions distinctes,
# si bien qu'on peut sortir deux « 5 » mais jamais deux « 100 », comme à la télé.
PETITES = list(range(1, 11)) * 2
GROSSES = [25, 50, 75, 100]
DECK_OFFICIEL = PETITES + GROSSES

CIBLE_MIN, CIBLE_MAX = 101, 999
NB_PLAQUES = 6

# ─────────────────────────── Indice de difficulté ───────────────────────────
#
# indice = W_RARETE / sqrt(n_solutions)   (peu de solutions ⇒ terme élevé)
#        + W_DIV  * nb de ÷ dans la solution la plus simple
#        + W_MUL  * nb de × dans la solution la plus simple
#
# Les divisions pèsent le plus (le plus dur au primaire), puis les
# multiplications ; la rareté ajoute la difficulté « combien de chemins existe-t-il ».
W_RARETE = 6.0
W_DIV = 4.0
W_MUL = 1.2

# Seuils croissants : indice < seuil ⇒ niveau associé ; au-delà du dernier, expert.
# Calés sur la structure plutôt que sur de purs percentiles : comme une division
# ajoute W_DIV (=4.0) à l'indice, « difficile » démarre là où la solution la plus
# simple impose une division, et « expert » là où il en faut plusieurs (ou que les
# chemins se raréfient fortement). Distribution observée (6 plaques, deck officiel) :
# ≈ 30 % facile, 43 % moyen, 18 % difficile, 9 % expert.
SEUILS = [(2.2, "facile"), (4.0, "moyen"), (7.0, "difficile")]
NIVEAUX = ("facile", "moyen", "difficile", "expert")

# Profil de lisibilité servant à choisir « la solution la plus simple » à noter.
NIVEAU_NOTATION = "primaire"


@dataclass
class Tirage:
    """Un tirage évalué : plaques, cible et sa difficulté mesurée."""

    plaques: list
    cible: int
    niveau: str
    indice: float
    n_solutions: int
    expression: str  # solution canonique la plus simple (entièrement parenthésée)
    n_div: int = 0
    n_mul: int = 0

    @property
    def ligne(self) -> str:
        """Solution la plus simple en ligne compacte (``8 × 50 + 3``…)."""
        return R.compact(R.parse(self.expression))


# ─────────────────────────── Mesures ───────────────────────────

def _atteignables(plaques):
    """Ensemble des valeurs atteignables avec **toutes** les plaques."""
    n = len(plaques)
    max_mask = 1 << n
    reach = _reachable(plaques, partitions_by_mask(n), max_mask)
    return reach[max_mask - 1]


def _compter_ops(node) -> tuple:
    """(nb de ÷, nb de ×) dans un arbre d'expression."""
    div = mul = 0

    def visite(n):
        nonlocal div, mul
        if isinstance(n, R.Op):
            if n.op == "/":
                div += 1
            elif n.op == "*":
                mul += 1
            visite(n.left)
            visite(n.right)

    visite(node)
    return div, mul


def _solutions_distinctes(solutions) -> int:
    """Nombre de solutions distinctes *par ligne compacte* (cf. ``readability``)."""
    return len({R.compact(R.parse(e)) for e in solutions})


def indice_difficulte(n_solutions: int, n_div: int, n_mul: int) -> float:
    """Indice continu de difficulté (plus haut = plus dur). Réglable (voir poids)."""
    return W_RARETE / math.sqrt(n_solutions) + W_DIV * n_div + W_MUL * n_mul


def niveau_pour(indice: float) -> str:
    """Convertit un indice en niveau nommé selon ``SEUILS``."""
    for seuil, nom in SEUILS:
        if indice < seuil:
            return nom
    return "expert"


def evaluer(plaques, cible, notation=NIVEAU_NOTATION, model=models.DEFAULT):
    """Évalue la difficulté d'un tirage donné.

    Retourne un ``Tirage`` ou ``None`` si la cible n'a **aucune** solution exacte
    (toutes les plaques). La difficulté combine la rareté des solutions et la
    dureté (÷ puis ×) de la solution la plus simple.
    """
    solutions = models.get(model).solve(list(plaques), cible)
    if not solutions:
        return None
    n_sol = _solutions_distinctes(solutions)
    plus_simple = R.top(solutions, 1, notation)[0]
    node = R.parse(plus_simple)
    n_div, n_mul = _compter_ops(node)
    idx = indice_difficulte(n_sol, n_div, n_mul)
    return Tirage(
        plaques=list(plaques),
        cible=cible,
        niveau=niveau_pour(idx),
        indice=round(idx, 2),
        n_solutions=n_sol,
        expression=plus_simple,
        n_div=n_div,
        n_mul=n_mul,
    )


# ─────────────────────────── Génération ───────────────────────────

def generer(
    niveau=None,
    n=NB_PLAQUES,
    deck=DECK_OFFICIEL,
    cible_min=CIBLE_MIN,
    cible_max=CIBLE_MAX,
    notation=NIVEAU_NOTATION,
    model=models.DEFAULT,
    seed=None,
    rng=None,
    essais=4000,
):
    """Génère un tirage (avec solution exacte garantie), au niveau demandé.

    - ``niveau`` : ``facile``/``moyen``/``difficile``/``expert``, ou ``None``
      pour accepter le premier tirage venu (et le laisser s'étiqueter seul) ;
    - ``n`` : nombre de plaques (6 par défaut, comme le jeu) ;
    - ``deck`` : réservoir de tirage (``DECK_OFFICIEL`` par défaut ; une liste
      avec doublons pour autoriser les plaques en double) ;
    - ``cible_min``/``cible_max`` : plage de la cible (utile pour adapter au
      primaire avec de plus petites cibles) ;
    - ``seed``/``rng`` : pour des tirages reproductibles.

    La cible est tirée **dans l'ensemble atteignable**, ce qui garantit une
    solution exacte sans rejet. ``RuntimeError`` si le niveau demandé n'a pas
    été atteint en ``essais`` tentatives (deck ou plage trop contraints).
    """
    if niveau is not None and niveau not in NIVEAUX:
        raise ValueError(f"Niveau inconnu : {niveau!r}. Disponibles : {', '.join(NIVEAUX)}")
    if rng is None:
        rng = random.Random(seed)

    for _ in range(essais):
        plaques = rng.sample(deck, n)
        cibles = [v for v in _atteignables(plaques) if cible_min <= v <= cible_max]
        if not cibles:
            continue
        cible = rng.choice(cibles)
        tirage = evaluer(plaques, cible, notation, model)
        if tirage is None:
            continue  # ne devrait pas arriver : cible ∈ atteignables
        if niveau is None or tirage.niveau == niveau:
            return tirage

    raise RuntimeError(
        f"Niveau {niveau!r} non atteint en {essais} essais "
        f"(deck/plage trop contraints ?)."
    )


def generer_serie(niveaux=NIVEAUX, **kwargs):
    """Un tirage par niveau (mêmes paramètres pour tous). Pratique pour une fiche."""
    return [generer(niveau=nv, **kwargs) for nv in niveaux]


# ─────────────────────────── CLI ───────────────────────────

def _afficher(tirage):
    lignes = [
        "═" * 64,
        f"  Le compte est bon — tirage « {tirage.niveau} »",
        "═" * 64,
        f"  Plaques : {tirage.plaques}",
        f"  Cible   : {tirage.cible}",
        f"  Niveau  : {tirage.niveau}  (indice {tirage.indice} ; "
        f"{tirage.n_solutions} solution(s), {tirage.n_div}÷ {tirage.n_mul}× au plus simple)",
        "─" * 64,
        "  Solution la plus simple :",
        "",
        R.format_solution(tirage.expression, tirage.cible),
    ]
    print("\n".join(lignes))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Génère des tirages « Le compte est bon » à difficulté graduée."
    )
    parser.add_argument("--niveau", "-N", choices=NIVEAUX,
                        help="niveau visé (sinon : premier tirage venu, étiqueté seul)")
    parser.add_argument("--serie", action="store_true",
                        help="un tirage par niveau (facile → expert)")
    parser.add_argument("--plaques", "-n", type=int, default=NB_PLAQUES,
                        help=f"nombre de plaques (défaut : {NB_PLAQUES})")
    parser.add_argument("--cible-min", type=int, default=CIBLE_MIN)
    parser.add_argument("--cible-max", type=int, default=CIBLE_MAX)
    parser.add_argument("--seed", type=int, help="graine pour un tirage reproductible")
    args = parser.parse_args(argv)

    commun = dict(n=args.plaques, cible_min=args.cible_min, cible_max=args.cible_max,
                  seed=args.seed)
    try:
        if args.serie:
            for tirage in generer_serie(**commun):
                _afficher(tirage)
        else:
            _afficher(generer(niveau=args.niveau, **commun))
    except RuntimeError as e:
        parser.error(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
