"""Tests des solveurs spécialisés best_first et closest."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import best_first as BF  # noqa: E402
import closest as CL  # noqa: E402
import models  # noqa: E402
import readability as R  # noqa: E402
from benchmark.cases import CASES  # noqa: E402


def _eval(expr):
    return eval(expr.replace(" ", ""))  # entrée canonique contrôlée


def test_best_first_retrouve_le_top_enumeration():
    """best_first donne le même top-K que l'énumération exhaustive triée."""
    extra = [([1, 2, 3, 4, 5, 6, 7], 100)]  # cas à beaucoup de solutions
    for nombres, cible in CASES + extra:
        full = models.get(models.DEFAULT).solve(list(nombres), cible)
        if not full:
            assert BF.solve(nombres, cible) == []
            continue
        for level in ("primaire", "college"):
            ref = R.top(full, 5, level)
            assert BF.solve(nombres, cible, 5, level) == ref, (nombres, cible, level)


def test_best_first_expressions_valides():
    exprs = BF.solve([1, 2, 3, 4, 5, 6, 7], 100, 5)
    assert exprs
    for e in exprs:
        assert _eval(e) == 100
        assert sorted(int(x) for x in re.findall(r"\d+", e)) == [1, 2, 3, 4, 5, 6, 7]


def test_closest_exact():
    """Cible atteignable : écart nul et solutions valides."""
    valeur, ecart, exprs = CL.solve([5, 75, 2, 50, 100, 10], 868)
    assert valeur == 868 and ecart == 0
    assert exprs and all(_eval(e) == 868 for e in exprs)


def test_closest_inatteignable():
    """Cible impossible : on vise la valeur atteignable la plus proche."""
    cible = 813
    valeur, ecart, exprs = CL.solve([100, 25, 7, 3], cible)
    # toutes les valeurs atteignables et la distance minimale
    full_mask = (1 << 4) - 1
    from models._masks import partitions_by_mask
    atteignables = BF._reachable([100, 25, 7, 3], partitions_by_mask(4), 1 << 4)[full_mask]
    assert cible not in atteignables
    assert ecart == valeur - cible
    assert abs(ecart) == min(abs(v - cible) for v in atteignables)
    assert exprs and all(_eval(e) == valeur for e in exprs)


if __name__ == "__main__":
    test_best_first_retrouve_le_top_enumeration()
    test_best_first_expressions_valides()
    test_closest_exact()
    test_closest_inatteignable()
    print("✓ Tests solveurs OK")
