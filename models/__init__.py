"""Registre des modèles de résolution de « Le compte est bon ».

Tous les modèles partagent la même sémantique et la même interface :

    solve(nombres: list[int], cible: int) -> set[str]

Sémantique : utiliser **toutes** les plaques exactement une fois. Opérations
+, -, *, / ; résultats intermédiaires entiers strictement positifs ; divisions
exactes uniquement. Le rendu des expressions est centralisé (voir _render.py),
si bien que tous les modèles renvoient des ensembles de chaînes comparables.
"""

from . import (
    m1_brute_state,
    m2_brute_recursive,
    m3_dp_mask_exprs,
    m4_memo_indices,
    m5_dp_bottomup,
    m6_twophase_cartesian,
    m7_twophase_memo,
    m8_twophase_targeted,
    m9_numpy_vectorized,
)

_MODULES = [
    m1_brute_state,
    m2_brute_recursive,
    m3_dp_mask_exprs,
    m4_memo_indices,
    m5_dp_bottomup,
    m6_twophase_cartesian,
    m7_twophase_memo,
    m8_twophase_targeted,
    m9_numpy_vectorized,
]

# nom -> module
REGISTRY = {m.NAME: m for m in _MODULES}

# Ordre stable d'affichage / de benchmark (du plus naïf au plus optimisé)
ORDER = [m.NAME for m in _MODULES]

DEFAULT = m8_twophase_targeted.NAME


def get(name):
    """Retourne le module de modèle ou lève KeyError avec un message utile."""
    try:
        return REGISTRY[name]
    except KeyError:
        dispo = ", ".join(ORDER)
        raise KeyError(f"Modèle inconnu : {name!r}. Disponibles : {dispo}") from None


def list_models():
    """Liste de (nom, origine, description) dans l'ordre stable."""
    return [(REGISTRY[n].NAME, REGISTRY[n].ORIGIN, REGISTRY[n].DESCRIPTION) for n in ORDER]
