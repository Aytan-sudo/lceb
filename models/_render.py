"""Rendu canonique des expressions, partagé par tous les modèles.

Objectif : garantir que deux modèles différents produisent *exactement* la
même chaîne pour une même opération, afin que leurs ensembles de solutions
soient comparables octet pour octet (validation croisée et benchmark).

Convention retenue : ordre canonique par **chaîne** pour les opérateurs
commutatifs (+ et *). C'est l'ordre déjà utilisé par la majorité des
algorithmes d'origine (main3, main6, main7, main8, main9).
"""


def feuille(valeur: int) -> str:
    """Expression d'une plaque seule."""
    return str(valeur)


def add(ea: str, eb: str) -> str:
    """Addition, commutative → opérandes triées par chaîne."""
    return f"({ea} + {eb})" if ea <= eb else f"({eb} + {ea})"


def mul(ea: str, eb: str) -> str:
    """Multiplication, commutative → opérandes triées par chaîne."""
    return f"({ea} * {eb})" if ea <= eb else f"({eb} * {ea})"


def sub(grand: str, petit: str) -> str:
    """Soustraction (l'appelant garantit grand - petit > 0)."""
    return f"({grand} - {petit})"


def div(numerateur: str, denominateur: str) -> str:
    """Division exacte (l'appelant garantit un quotient entier > 0)."""
    return f"({numerateur} / {denominateur})"
