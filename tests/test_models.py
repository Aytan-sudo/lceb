"""Validation croisée de tous les modèles.

Garanties vérifiées pour chaque cas :
  1. Validité  : chaque expression s'évalue exactement à la cible.
  2. Toutes plaques : chaque expression utilise exactement les plaques données.
  3. Concordance : tous les modèles renvoient le **même** ensemble de solutions.

Exécutable tel quel (`uv run python tests/test_models.py`) ou via pytest.
"""

import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import models  # noqa: E402
from benchmark.cases import CASES  # noqa: E402


def _eval(expr):
    s = expr.replace(" ", "")
    if not re.fullmatch(r"[\d+\-*/()]+", s):
        return None
    try:
        r = eval(s)  # entrée contrôlée (regex ci-dessus)
    except ZeroDivisionError:
        return None
    return int(r) if r == int(r) else r


def _plaques(expr):
    return sorted(int(x) for x in re.findall(r"\d+", expr))


def _verifie_cas(nombres, cible):
    attendu_plaques = sorted(nombres)
    ensembles = {}
    for nom in models.ORDER:
        sols = models.get(nom).solve(list(nombres), cible)
        for s in sols:
            assert _eval(s) == cible, f"{nom}: {s} ≠ {cible}"
            assert _plaques(s) == attendu_plaques, f"{nom}: plaques incorrectes dans {s}"
        ensembles[nom] = sols

    ref_nom = models.DEFAULT
    ref = ensembles[ref_nom]
    for nom, sols in ensembles.items():
        assert sols == ref, (
            f"{nom} diverge de {ref_nom} sur {nombres}→{cible} : "
            f"+{sorted(sols - ref)[:3]} -{sorted(ref - sols)[:3]}"
        )
    return len(ref)


def test_cas_standards():
    for nombres, cible in CASES:
        _verifie_cas(nombres, cible)


def test_tirages_aleatoires():
    rng = random.Random(1234)
    for _ in range(15):
        nombres = [rng.randint(1, 100) for _ in range(rng.randint(3, 5))]
        cible = rng.randint(1, 600)
        _verifie_cas(nombres, cible)


if __name__ == "__main__":
    total = 0
    for nombres, cible in CASES:
        n = _verifie_cas(nombres, cible)
        print(f"  ✓ {nombres} → {cible} : {n} solution(s), 9 modèles concordent")
        total += 1
    test_tirages_aleatoires()
    print(f"  ✓ 15 tirages aléatoires : 9 modèles concordent")
    print(f"\n✓ Tous les tests passent ({total} cas standards + 15 aléatoires).")
