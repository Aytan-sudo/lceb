"""Couche de présentation « lisible pour le primaire ».

Les modèles renvoient des expressions entièrement parenthésées
(ex. ``(((10 * 100) - 2) - 5)``). Ce module les rend digestes pour un enfant :

  1. on re-parse l'expression en arbre (sans ambiguïté car tout est parenthésé) ;
  2. on lui attribue un **score de lisibilité** (plus bas = plus simple) ;
  3. on l'affiche de deux façons : une **ligne compacte** (parenthèses minimales)
     et le **détail pas-à-pas** (une opération par ligne, comme à la télé).

Philosophie du score
--------------------
Ce qui rend un calcul facile pour un enfant n'est pas tant la *forme* de
l'arbre (linéaire vs « chunké » comme (8+2)+(10−3)) que **la difficulté de
chaque opération prise isolément** : opérer sur de petits nombres ronds avec
des + et des − est facile ; manipuler de grands nombres, multiplier ou diviser
est dur. Le chunking n'est donc pas pénalisé en tant que tel — il l'est
seulement, et faiblement, par la charge en mémoire de travail (devoir retenir
deux sous-résultats au lieu d'un seul accumulateur).

Le score (plus bas = plus simple) combine, par ordre d'importance :
  1. le nombre de **divisions** (clé prioritaire — c'est le plus dur au primaire) ;
  2. un **coût mêlé** : multiplications, taille des nombres manipulés, étapes
     ``×1`` / ``÷1`` inutiles, résultats non ronds, et un petit terme de
     mémoire de travail pour départager.
Les poids sont réglables ci-dessous (section « Poids du score »).
"""

from dataclasses import dataclass

# Symboles d'affichage (les opérateurs internes restent +, -, *, /).
SYM = {"+": "+", "-": "−", "*": "×", "/": "÷"}
PREC = {"+": 1, "-": 1, "*": 2, "/": 2}


@dataclass
class Leaf:
    value: int


@dataclass
class Op:
    op: str
    left: "Node"
    right: "Node"
    value: int


Node = "Leaf | Op"


# ──────────────────────────── Parsing ────────────────────────────

def parse(expr: str) -> Node:
    """Parse une expression entièrement parenthésée en arbre.

    Grammaire : ``expr := nombre | "(" expr " " op " " expr ")"``.
    """
    pos = 0

    def parse_expr():
        nonlocal pos
        if expr[pos] == "(":
            pos += 1                      # '('
            left = parse_expr()
            pos += 1                      # ' '
            op = expr[pos]
            pos += 2                      # op + ' '
            right = parse_expr()
            pos += 1                      # ')'
            return Op(op, left, right, _apply(op, left.value, right.value))
        start = pos
        while pos < len(expr) and expr[pos].isdigit():
            pos += 1
        return Leaf(int(expr[start:pos]))

    return parse_expr()


def _apply(op, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return a // b


# ──────────────────────────── Score ────────────────────────────
#
# Profils de poids selon le niveau scolaire. Chaque poids : augmenter =
# rendre ce trait plus pénalisant, donc plus rare en tête de classement.
#
#   mul      : pénalité par multiplication (moins naturelle qu'un + ou −)
#   digit    : coût par chiffre des opérandes (élevé ⇒ favorise les petits nombres)
#   nonround : intermédiaire non rond (ni multiple de 10 ni de 5)
#   trivial  : ×1 ou ÷1 (étape inutile)
#   memory   : charge mémoire = nb de sous-résultats à tenir en parallèle
#   paren    : pénalité par parenthèse (élevé ⇒ favorise les chaînes plates)
#
# - « primaire » : un seul total qui évolue. On ignore la taille des nombres
#   (digit=0) et on pousse fort vers les chaînes plates (memory + paren élevés).
# - « college »  : l'élève peut tenir deux nombres. On favorise les petits
#   nombres (digit élevé), quitte à grouper (memory + paren faibles).
PROFILES = {
    "primaire": dict(mul=3.0, digit=0.0, nonround=1.0, trivial=6.0, memory=2.5, paren=2.0),
    "college":  dict(mul=3.0, digit=1.0, nonround=1.5, trivial=6.0, memory=0.3, paren=0.0),
}
DEFAULT_LEVEL = "primaire"


def _round_penalty(v: int) -> int:
    if v % 10 == 0:
        return 0
    if v % 5 == 0:
        return 1
    return 2


def _digits(v: int) -> int:
    return len(str(abs(v)))


def _registers(n: Node) -> int:
    """Nombre minimal de sous-résultats à garder en tête (Sethi–Ullman).

    Une chaîne accumulateur ⇒ 2 ; un arbre équilibré (a∘b)∘(c∘d) ⇒ 3.
    L'écart est faible, d'où un poids (W_MEMORY) volontairement modeste.
    """
    if isinstance(n, Leaf):
        return 1
    g, d = _registers(n.left), _registers(n.right)
    return g + 1 if g == d else max(g, d)


def score(node: Node, level: str = DEFAULT_LEVEL):
    """Clé de tri : plus petite = plus lisible, selon le profil ``level``.

    (divisions, coût_mêlé, longueur, texte). La division reste la clé
    prioritaire ; le reste est un coût continu pondéré (cf. PROFILES).
    Les deux dernières composantes ne servent qu'à départager de façon stable.
    """
    w = PROFILES[level]
    div = 0
    cout = 0.0

    def visite(n):
        nonlocal div, cout
        if isinstance(n, Leaf):
            return
        visite(n.left)
        visite(n.right)
        if n.op == "/":
            div += 1
        elif n.op == "*":
            cout += w["mul"]
        cout += w["digit"] * (_digits(n.left.value) + _digits(n.right.value))
        cout += w["nonround"] * _round_penalty(n.value)
        if n.op in ("*", "/") and (n.left.value == 1 or n.right.value == 1):
            cout += w["trivial"]  # ×1 / ÷1 : opération qui ne sert à rien

    visite(node)
    cout += w["memory"] * _registers(node)
    compact_str = compact(node)
    cout += w["paren"] * compact_str.count("(")
    return (div, cout, len(compact_str), compact_str)


# ──────────────────────── Rendu compact ────────────────────────

def compact(node: Node, parent_op: str | None = None, side: str | None = None) -> str:
    """Expression sur une ligne, parenthèses réduites au strict nécessaire."""
    if isinstance(node, Leaf):
        return str(node.value)

    gauche = compact(node.left, node.op, "L")
    droite = compact(node.right, node.op, "R")
    texte = f"{gauche} {SYM[node.op]} {droite}"

    if parent_op is None:
        return texte

    besoin = PREC[node.op] < PREC[parent_op]
    # Même priorité : seul l'opérande droit d'un opérateur non associatif
    # (− ou ÷) a besoin de parenthèses (ex. a − (b − c), a ÷ (b × c)).
    if not besoin and PREC[node.op] == PREC[parent_op] and side == "R" and parent_op in ("-", "/"):
        besoin = True

    return f"({texte})" if besoin else texte


# ──────────────────────── Rendu pas-à-pas ────────────────────────

def steps(node: Node):
    """Liste des opérations dans l'ordre de calcul (post-ordre).

    Chaque élément est ``(gauche, op, droite, resultat)`` avec des valeurs
    numériques — un enfant lit directement les nombres.
    """
    out = []

    def visite(n):
        if isinstance(n, Leaf):
            return n.value
        g = visite(n.left)
        d = visite(n.right)
        out.append((g, n.op, d, n.value))
        return n.value

    visite(node)
    return out


def format_solution(expr: str, cible: int, numero: int | None = None) -> str:
    """Rendu complet d'une solution : ligne compacte + pas-à-pas."""
    node = parse(expr)
    etapes = steps(node)
    largeur = max(len(f"{g} {SYM[op]} {d}") for g, op, d, _ in etapes)

    entete = f"  {expr_compact(node)} = {cible}"
    if numero is not None:
        entete = f"  {numero}. {expr_compact(node)} = {cible}"

    lignes = [entete]
    for g, op, d, res in etapes:
        calcul = f"{g} {SYM[op]} {d}"
        lignes.append(f"        {calcul:<{largeur}} = {res}")
    return "\n".join(lignes)


def expr_compact(node: Node) -> str:
    """Ligne compacte (sans le « = cible »)."""
    return compact(node)


def top(solutions, k: int = 5, level: str = DEFAULT_LEVEL):
    """Retourne les ``k`` expressions les plus lisibles, triées (plus simple d'abord).

    Les solutions sont dédoublonnées par **ligne compacte** : deux arbres qui
    s'écrivent pareil (ex. (8+2)+(10−3) et ((8+2)+10)−3 → « 8 + 2 + 10 − 3 »)
    ne comptent que pour une, et on en garde le chemin de calcul le plus simple
    pour le niveau demandé.
    """
    meilleur = {}  # ligne compacte -> (score, expr)
    for expr in solutions:
        node = parse(expr)
        cle = compact(node)
        sc = score(node, level)
        if cle not in meilleur or sc < meilleur[cle][0]:
            meilleur[cle] = (sc, expr)
    ordonne = sorted(meilleur.values(), key=lambda se: se[0])
    return [expr for _, expr in ordonne[:k]]
