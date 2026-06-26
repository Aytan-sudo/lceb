"""Tests du générateur de tirages à difficulté graduée."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generate as G  # noqa: E402


def _eval(expr):
    return eval(expr.replace(" ", ""))  # entrée canonique contrôlée


def test_solution_exacte_garantie():
    """Tout tirage généré a une solution exacte utilisant toutes les plaques."""
    rng = __import__("random").Random(123)
    for _ in range(20):
        t = G.generer(rng=rng)
        assert _eval(t.expression) == t.cible
        plaques_utilisees = sorted(int(x) for x in re.findall(r"\d+", t.expression))
        assert plaques_utilisees == sorted(t.plaques)


def test_niveau_demande_respecte():
    """Le tirage rendu porte bien le niveau demandé."""
    for niveau in G.NIVEAUX:
        t = G.generer(niveau, seed=7)
        assert t.niveau == niveau


def test_reproductible_avec_seed():
    a = G.generer("moyen", seed=99)
    b = G.generer("moyen", seed=99)
    assert (a.plaques, a.cible) == (b.plaques, b.cible)


def test_serie_un_par_niveau():
    serie = G.generer_serie(seed=3)
    assert [t.niveau for t in serie] == list(G.NIVEAUX)


def test_evaluer_sans_solution():
    """Cible hors d'atteinte → evaluer renvoie None."""
    # 4 petites plaques : impossible d'atteindre une grande cible exactement.
    assert G.evaluer([1, 2, 3, 4], 999) is None


def test_indice_monotone_par_niveau():
    """Les seuils ordonnent bien : niveau_pour est croissant avec l'indice."""
    rangs = {nom: i for i, nom in enumerate(G.NIVEAUX)}
    for indice in (0.5, 2.0, 3.0, 5.0, 8.0, 12.0):
        nom = G.niveau_pour(indice)
        nom_sup = G.niveau_pour(indice + 0.01)
        assert rangs[nom_sup] >= rangs[nom]


def test_plage_cible_respectee():
    t = G.generer(cible_min=200, cible_max=400, seed=11)
    assert 200 <= t.cible <= 400


if __name__ == "__main__":
    test_solution_exacte_garantie()
    test_niveau_demande_respecte()
    test_reproductible_avec_seed()
    test_serie_un_par_niveau()
    test_evaluer_sans_solution()
    test_indice_monotone_par_niveau()
    test_plage_cible_respectee()
    print("✓ Tests générateur OK")
