"""Tests de la couche de présentation (readability.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import models  # noqa: E402
import readability as R  # noqa: E402
from benchmark.cases import CASES  # noqa: E402


def test_parse_et_valeur():
    """L'arbre re-parsé reconstitue exactement la cible et le calcul pas-à-pas."""
    for nombres, cible in CASES:
        for expr in models.get(models.DEFAULT).solve(list(nombres), cible):
            node = R.parse(expr)
            assert node.value == cible, f"{expr} : valeur {node.value} ≠ {cible}"
            etapes = R.steps(node)
            assert etapes[-1][3] == cible, f"{expr} : dernière étape ≠ {cible}"
            # nombre d'étapes = nombre d'opérations = nb_plaques - 1
            assert len(etapes) == len(nombres) - 1


def test_compact_sans_parentheses_superflues():
    """Une chaîne linéaire de soustractions n'a aucune parenthèse."""
    node = R.parse("((((10 * 100) - 5) - 75) - 2)")
    assert R.compact(node) == "10 × 100 − 5 − 75 − 2"


def test_compact_parentheses_necessaires():
    """Les parenthèses indispensables sont conservées."""
    assert R.compact(R.parse("(100 / (9 - 7))")) == "100 ÷ (9 − 7)"
    assert R.compact(R.parse("(8 - (3 - 1))")) == "8 − (3 − 1)"
    assert R.compact(R.parse("(8 - (3 + 1))")) == "8 − (3 + 1)"
    # opérande droit d'un + à même priorité : pas de parenthèses
    assert R.compact(R.parse("(8 + (3 - 1))")) == "8 + 3 − 1"


def test_score_prefere_moins_de_divisions():
    sans_div = R.parse("((10 * 100) - 2)")
    avec_div = R.parse("((10 * 100) / 2)")
    assert R.score(sans_div) < R.score(avec_div)


def test_top_est_trie_et_borne():
    sols = models.get(models.DEFAULT).solve([5, 75, 2, 50, 100, 10], 868)
    meilleures = R.top(sols, 5)
    assert len(meilleures) == 5
    cles = [R.score(R.parse(e)) for e in meilleures]
    assert cles == sorted(cles)


def test_niveaux_changent_le_classement():
    """primaire favorise le séquentiel (chaîne plate), college le groupé."""
    sols = models.get(models.DEFAULT).solve([5, 75, 2, 50, 100, 10], 868)
    prim = R.compact(R.parse(R.top(sols, 1, "primaire")[0]))
    coll = R.compact(R.parse(R.top(sols, 1, "college")[0]))
    assert "(" not in prim          # primaire : chaîne plate, sans parenthèses
    assert "(" in coll              # college : regroupe → parenthèses
    assert prim != coll


if __name__ == "__main__":
    test_parse_et_valeur()
    test_compact_sans_parentheses_superflues()
    test_compact_parentheses_necessaires()
    test_score_prefere_moins_de_divisions()
    test_top_est_trie_et_borne()
    print("✓ Tests readability OK")
