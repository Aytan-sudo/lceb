# Le compte est bon

Résolution exhaustive du jeu **« Le compte est bon »** : trouver toutes les
expressions arithmétiques qui atteignent une cible à partir de plaques données.

Le projet rassemble **9 algorithmes** différents (du plus naïf au plus optimisé),
tous harmonisés derrière une interface unique pour pouvoir les comparer
équitablement.

## Règles implémentées

- Opérations : `+`, `-`, `*`, `/`.
- Chaque plaque est utilisée **exactement une fois** (toutes les plaques).
- Résultats intermédiaires : entiers **strictement positifs**.
- Divisions **exactes** uniquement.
- Les symétries triviales de `+` et `*` sont dédoublonnées (ordre canonique).

## Structure

```
solve.py              Point d'entrée unique : fonction solve() + CLI
models/               Les 9 modèles de résolution
  _render.py          Rendu canonique partagé (mêmes chaînes pour tous)
  _masks.py           Pré-calcul des partitions (modèles deux-phases)
  m1..m9_*.py         Un fichier par algorithme
benchmark/            Comparaison équitable (mêmes entrées pour tous)
  cases.py            Cas d'entrée partagés
  bench.py            Chronométrage + vérification de cohérence
tests/                Validation croisée (tous les modèles concordent)
archive/original/     Les scripts d'origine (main1.py … main9_improved.py)
```

## Utilisation

### En ligne de commande

```bash
uv run python solve.py --nb 5 75 2 50 100 10 --cible 868
uv run python solve.py --model brute_state --nb 100 9 7 1 --cible 50
uv run python solve.py --list          # liste des modèles disponibles
```

### En bibliothèque

```python
from solve import solve

solutions = solve("twophase_targeted", [5, 75, 2, 50, 100, 10], 868)
print(len(solutions))   # -> 116
```

## Benchmark

```bash
uv run python benchmark/bench.py            # cas standards
uv run python benchmark/bench.py --heavy    # ajoute un cas à 7 plaques
uv run python benchmark/bench.py --iters 10
```

Le benchmark exécute tous les modèles **dans le même processus, sur les mêmes
entrées**, et vérifie qu'ils renvoient le **même** ensemble de solutions.

## Tests

```bash
uv run python tests/test_models.py     # ou : uv run pytest
```

## Les modèles

| Modèle | Origine | Idée |
|---|---|---|
| `brute_state` | main1 | Force brute récursive, sans cache |
| `brute_recursive` | main2 | Force brute récursive |
| `dp_mask_exprs` | main3 | DP descendante par masque, dict valeur→expressions |
| `memo_indices` | main4 | Mémoïsation sur ensembles d'index |
| `dp_bottomup` | main5 | DP ascendante itérative |
| `twophase_cartesian` | main6 | Reachability + reconstruction cartésienne |
| `twophase_memo` | main7 | Reachability ascendante + memo manuel |
| `twophase_targeted` | main8 | **Reconstruction ciblée** — le plus rapide |
| `numpy_vectorized` | main9 | Reachability vectorisée NumPy |

> Note : le `multiprocessing` du modèle 9 d'origine a été retiré — à cette
> échelle (≤ 9 plaques) son surcoût dépasse tout gain et il rendait le module
> fragile à l'import.
