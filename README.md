# pd_quality

`pd_quality` est une librairie légère qui s'intègre directement à Pandas pour auditer rapidement la santé de vos DataFrames.
Elle ajoute un accesseur `.quality` à n'importe quel `DataFrame` et génère un rapport visuel (terminal ou Jupyter) sans avoir à réécrire les mêmes lignes Pandas à chaque projet.

## Installation

```bash
# version texte minimale
pip install pd_quality

# version visuelle (recommandée) — ajoute le rendu coloré en terminal
pip install "pd_quality[rich]"
```

## Utilisation

```python
import pandas as pd
import pd_quality  # enregistre l'accesseur df.quality

df = pd.read_csv("mes_donnees.csv")
df.quality.report()
```

## Aperçu

### Terminal (avec `rich`)

```text
╭───────────────────────────── 📊 Vue d'ensemble ──────────────────────────────╮
│ Lignes   Colonnes   Mémoire   Doublons                                       │
│ 1,003       6       0.19 MB      3                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────── 🔍 Valeurs manquantes ────────────────────────────╮
│ ┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Colonne      ┃      Manquants ┃        % ┃ Distribution                  ┃ │
│ ┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ segment      │            301 │    30.0% │ ██████░░░░░░░░░░░░░░          │ │
│ │ age          │             81 │     8.1% │ ██░░░░░░░░░░░░░░░░░░          │ │
│ │ city         │             50 │     5.0% │ █░░░░░░░░░░░░░░░░░░░          │ │
│ └──────────────┴────────────────┴──────────┴───────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────── 🏷️  Types ──────────────────────────────────╮
│ str      3                                                                   │
│ float64  2                                                                   │
│ int64    1                                                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────── 💡 Remarques ────────────────────────────────╮
│ ⚠ Colonnes constantes (1) : country                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

> Dans un vrai terminal, les pourcentages et barres sont colorés : **vert** < 5 %, **jaune** 5–30 %, **rouge** ≥ 30 %.

### Jupyter Notebook

Dans un notebook, le même appel renvoie automatiquement un rendu HTML : KPI cards, mini-barres de progression CSS, badges colorés. Aucune action supplémentaire — l'environnement est détecté automatiquement.

## Ce que le rapport contient

- **Vue d'ensemble** : nombre de lignes / colonnes, empreinte mémoire, doublons
- **Valeurs manquantes** : count, pourcentage et barre de distribution par colonne (triés du pire au meilleur)
- **Types** : récapitulatif des dtypes
- **Remarques** : colonnes constantes (souvent à supprimer) et colonnes 100 % uniques (candidates clé primaire)

## API

```python
report = df.quality.report()                 # affiche + retourne l'objet
report = df.quality.report(display=False)    # silencieux, retourne juste l'objet

# Accès programmatique
report.to_dict()         # dict complet
report["shape"]          # accès par clé (rétro-compatible)
report.missing           # DataFrame des manquants
report.constant_cols     # liste
report.unique_cols       # liste
```

Méthodes individuelles disponibles si tu n'as besoin que d'un check :

```python
df.quality.check_missing()     # DataFrame: Missing, Percentage (%)
df.quality.check_duplicates()  # int
df.quality.check_types()       # Series des dtypes
```

## Licence

MIT — voir `LICENSE`.
