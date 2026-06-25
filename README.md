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
solve.py              Point d'entrée unique : fonction solve() + CLI (3 modes)
readability.py        Rendu lisible enfant : score + ligne compacte + pas-à-pas
best_first.py         Solveur top-K direct (k-best) sans tout énumérer
closest.py            Solveur « le plus proche » si la cible est inatteignable
models/               Les 9 modèles d'énumération exhaustive
  _render.py          Rendu canonique partagé (mêmes chaînes pour tous)
  _masks.py           Pré-calcul des partitions (modèles deux-phases)
  m1..m9_*.py         Un fichier par algorithme
benchmark/            Comparaisons
  cases.py            Cas d'entrée partagés
  bench.py            Comparaison équitable (mêmes entrées, vérif cohérence)
  bench_extreme.py    Cas durs, timeout par modèle (où chaque approche cède)
tests/                Validation croisée + tests rendu + tests solveurs
archive/original/     Les scripts d'origine (main1.py … main9_improved.py)
```

## Utilisation

### En ligne de commande

```bash
uv run python solve.py --nb 5 75 2 50 100 10 --cible 868
uv run python solve.py --nb 5 75 2 50 100 10 --cible 868 --top 3       # 3 meilleures
uv run python solve.py --nb 5 75 2 50 100 10 --cible 868 --lvl college # style collège
uv run python solve.py --nb 1 2 3 4 5 6 7 --cible 100 --mode best      # top-K direct
uv run python solve.py --nb 100 25 7 3 --cible 813 --mode closest      # le plus proche
uv run python solve.py --list          # liste des modèles disponibles
```

### Modes (`--mode`)

- **`all`** (défaut) : énumère **toutes** les solutions avec `--model`, en affiche
  les `--top` plus lisibles. Idéal pour 6 plaques (instantané).
- **`best`** : reconstruction *k-best* (`best_first.py`) — renvoie directement le
  top-K sans matérialiser l'ensemble. Pratique jusqu'à ~7 plaques ; **ce n'est pas
  un solveur qui passe à l'échelle** (à 8-9 plaques, la traversée domine comme
  pour l'énumération).
- **`closest`** : si la cible exacte est impossible, vise la **valeur atteignable
  la plus proche** (`closest.py`) — la vraie règle du jeu télévisé.

La sortie affiche les solutions **les plus lisibles** d'abord (cf. `readability.py`),
chacune en ligne compacte + détail pas-à-pas :

```
  1. 10 × 100 − 5 − 75 − 50 − 2 = 868
        10 × 100 = 1000
        1000 − 5 = 995
        995 − 75 = 920
        920 − 50 = 870
        870 − 2  = 868
```

Le score de lisibilité privilégie partout : peu de `÷` puis peu de `×`, des
résultats intermédiaires ronds, et pas d'étapes inutiles (`×1`, `÷1`). Le style
dépend du **niveau** (`--lvl`) :

- **`primaire`** (défaut) : un seul total qui évolue, méthode école/télé.
  Ex. `10 × 100 − 5 − 75 − 50 − 2` (un seul nombre à suivre, même s'il est grand).
- **`college`** : regroupe les petits nombres pour limiter les calculs sur de
  grands nombres. Ex. `10 × 100 − (5 + 75 + 50) − 2` (petits nombres, mais il
  faut en tenir deux en tête).

Les poids de chaque profil sont réglables en tête de `readability.py` (`PROFILES`).

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
uv run python benchmark/bench_extreme.py    # cas durs, timeout par modèle
```

`bench.py` exécute tous les modèles **dans le même processus, sur les mêmes
entrées**, et vérifie qu'ils renvoient le **même** ensemble de solutions.

`bench_extreme.py` vise les cas à **explosion de solutions** (jusqu'à ~1,1 M),
chaque modèle isolé avec timeout. On y voit nettement la hiérarchie : la force
brute cède en premier, puis les DP « dictionnaire d'expressions », tandis que
les deux-phases tiennent. `best_first` s'y aligne sur les meilleurs énumérateurs
(il borne la sortie, pas la traversée).

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
