"""Solveur « best-first » : les K solutions les plus lisibles, sans tout énumérer.

Les énumérateurs de ``models/`` construisent *toutes* les expressions (parfois
plus d'un million) avant qu'on n'en garde 5. Ici on fait une reconstruction
**k-best** : chaque sous-problème ``(masque, valeur)`` ne conserve que ses
``POOL`` meilleures expressions, par coût additif croissant.

Chaque sous-arbre candidat est classé par le **score de lisibilité complet** du
sous-arbre lui-même (et non par un coût purement additif) : c'est indispensable
pour que les composantes structurelles du score (mémoire de travail, parenthèses)
— qui distinguent le style « primaire » du style « collège » — soient prises en
compte dès la troncature des pools.

Intérêt par rapport aux énumérateurs de ``models/`` :
  - **top-K direct**, sans matérialiser ni trier l'ensemble géant des solutions ;
  - chaque sous-problème ne garde que ``POOL`` expressions au lieu de toutes.

Limite honnête : ce n'est **pas** un solveur qui passe à l'échelle. La
traversée de reachability — commune avec les énumérateurs — domine, et la
mémoïsation d'un pool pour *chaque* état ``(masque, valeur)`` fait exploser la
mémoire dès 8-9 plaques (≈ 1,5 Go / plusieurs minutes à 9 plaques). best_first
est pertinent jusqu'à ~7 plaques (le jeu réel en utilise 6) ; au-delà, le
problème lui-même (des millions de solutions) est intrinsèquement coûteux.

Note : la troncature par nœud est une **heuristique** (pool réglable). En
pratique, avec un pool large, il retrouve le même top-K que l'énumération
exhaustive (vérifié par les tests).
"""

from models import _render as RND
from models._masks import partitions_by_mask
import readability as R

NAME = "best_first"

# Correspondance étiquette → opérande affichée (gestion des sens inverses).
_TAGS = ("+", "*", "-", "-inv", "/", "/inv")


def _reachable(numbers, parts, max_mask):
    """Valeurs atteignables par sous-ensemble (phase 1, peu coûteuse)."""
    reach = [None] * max_mask
    for i, v in enumerate(numbers):
        reach[1 << i] = frozenset((v,))
    for mask in range(1, max_mask):
        if reach[mask] is not None:
            continue
        vals = set()
        for A, B in parts[mask]:
            for x in reach[A]:
                for y in reach[B]:
                    vals.add(x + y)
                    vals.add(x * y)
                    if x > y:
                        vals.add(x - y)
                    elif y > x:
                        vals.add(y - x)
                    if y and x % y == 0:
                        vals.add(x // y)
                    if x and y % x == 0:
                        vals.add(y // x)
        reach[mask] = frozenset(vals)
    return reach


def top_k_for(numbers, value, k=5, level=R.DEFAULT_LEVEL, pool=None):
    """Les ``k`` expressions les plus lisibles atteignant exactement ``value``.

    Retourne une liste de chaînes canoniques (vide si ``value`` inatteignable).
    """
    n = len(numbers)
    max_mask = 1 << n
    full = max_mask - 1
    parts = partitions_by_mask(n)
    reach = _reachable(numbers, parts, max_mask)
    if value not in reach[full]:
        return []

    w = R.PROFILES[level]
    POOL = pool if pool is not None else max(40, 8 * k)
    memo = {}

    # Un candidat est un enregistrement compact qui porte de quoi (a) l'élaguer
    # vite et (b) le combiner sans re-parser :
    #   (expr, op_racine, registres, parentheses, divisions, cout_additif)
    # « cout_additif » = somme, sur tous les nœuds, des composantes additives du
    # score (×, taille des nombres, rondeur, ×1/÷1). Voir readability.score.

    def _paren(parent_op, child_op, side):
        if child_op is None:
            return 0
        if R.PREC[child_op] < R.PREC[parent_op]:
            return 1
        if R.PREC[child_op] == R.PREC[parent_op] and side == "R" and parent_op in ("-", "/"):
            return 1
        return 0

    def _key(rec):
        # Clé d'élagage : proxy fidèle du score de lisibilité (sans le tie-break
        # par chaîne, inutile pour la troncature).
        _, _, regs, par, div, add = rec
        return (div, add + w["memory"] * regs + w["paren"] * par)

    def _make(expr, op, x, y, resval, lrec, rrec):
        _, lop, lregs, lpar, ldiv, ladd = lrec
        _, rop, rregs, rpar, rdiv, radd = rrec
        add = ladd + radd
        if op == "*":
            add += w["mul"]
        add += w["digit"] * (R._digits(x) + R._digits(y))
        add += w["nonround"] * R._round_penalty(resval)
        if op in ("*", "/") and (x == 1 or y == 1):
            add += w["trivial"]
        regs = lregs + 1 if lregs == rregs else max(lregs, rregs)
        par = lpar + rpar + _paren(op, lop, "L") + _paren(op, rop, "R")
        div = ldiv + rdiv + (1 if op == "/" else 0)
        return (expr, op, regs, par, div, add)

    def combine(cand, gauche, droite, tag, x, y, resval):
        op = "-" if tag in ("-", "-inv") else "/" if tag in ("/", "/inv") else tag
        for lrec in gauche:
            le = lrec[0]
            for rrec in droite:
                re = rrec[0]
                if tag == "+":
                    expr, a, b = RND.add(le, re), lrec, rrec
                elif tag == "*":
                    expr, a, b = RND.mul(le, re), lrec, rrec
                elif tag == "-":
                    expr, a, b = RND.sub(le, re), lrec, rrec       # x - y
                elif tag == "-inv":
                    expr, a, b = RND.sub(re, le), rrec, lrec       # y - x
                elif tag == "/":
                    expr, a, b = RND.div(le, re), lrec, rrec       # x / y
                else:
                    expr, a, b = RND.div(re, le), rrec, lrec       # y / x
                rec = _make(expr, op, x, y, resval, a, b)
                old = cand.get(expr)
                if old is None or _key(rec) < _key(old):
                    cand[expr] = rec

    def build(mask, val):
        key = (mask, val)
        if key in memo:
            return memo[key]

        if not (mask & (mask - 1)):
            idx = mask.bit_length() - 1
            res = [(str(numbers[idx]), None, 1, 0, 0, 0.0)] if numbers[idx] == val else []
            memo[key] = res
            return res

        cand = {}  # expr -> enregistrement
        for A, B in parts[mask]:
            sA, sB = reach[A], reach[B]
            for x in sA:                                  # addition
                y = val - x
                if y in sB:
                    combine(cand, build(A, x), build(B, y), "+", x, y, val)
            for x in sA:                                  # multiplication
                if x and val % x == 0 and (y := val // x) in sB:
                    combine(cand, build(A, x), build(B, y), "*", x, y, val)
            for x in sA:                                  # soustraction x - y
                y = x - val
                if y > 0 and y in sB:
                    combine(cand, build(A, x), build(B, y), "-", x, y, val)
            for x in sA:                                  # soustraction y - x
                y = x + val
                if y in sB:
                    combine(cand, build(A, x), build(B, y), "-inv", x, y, val)
            for y in sB:                                  # division x / y
                x = val * y
                if x in sA:
                    combine(cand, build(A, x), build(B, y), "/", x, y, val)
            for x in sA:                                  # division y / x
                y = val * x
                if y in sB:
                    combine(cand, build(A, x), build(B, y), "/inv", x, y, val)

        res = sorted(cand.values(), key=_key)[:POOL]
        memo[key] = res
        return res

    pooled = build(full, value)

    # Classement exact à la racine (score complet), dédoublonné par ligne compacte.
    meilleur = {}
    for rec in pooled:
        expr = rec[0]
        cle = R.compact(R.parse(expr))
        sc = R.score(R.parse(expr), level)
        if cle not in meilleur or sc < meilleur[cle][1]:
            meilleur[cle] = (expr, sc)
    ordonne = sorted(meilleur.values(), key=lambda es: es[1])
    return [expr for expr, _ in ordonne[:k]]


def solve(numbers, target, k=5, level=R.DEFAULT_LEVEL, pool=None):
    """Top-K solutions lisibles pour la cible exacte ([] si inatteignable)."""
    return top_k_for(numbers, target, k, level, pool)
