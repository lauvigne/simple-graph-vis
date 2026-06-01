# Marimo exploration dataviz

Prototype Python/Marimo pour explorer les mappings applicatifs. L'ingestion Excel est séparée des rapports:

- `ingest.py` charge l'Excel et réécrit `marimo/data/`
- `app.py` lit uniquement les tables DuckDB présentes dans `marimo/data/`
- `treemap.py` affiche un treemap des capacités métiers par applications ou incidents
- `ingest.py` peut aussi charger un JSON de configuration pour paramétrer les sources et les colonnes
- `config_builder.py` sert à éditer et sauvegarder le JSON de paramétrage dans Marimo

## Installation

```bash
cd marimo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
marimo run ingest.py
```

Puis:

```bash
marimo run app.py
```

Pour un contrôle non interactif:

```bash
python ingest.py
python app.py
python -m unittest discover -s tests
```

## Stockage

La cible est un simple fichier DuckDB local:

- `marimo/data/local.duckdb`

Le répertoire `marimo/data/` contient aussi les fichiers temporaires éventuellement créés par l’ingestion.

## Principe

Les cellules Marimo restent fines. La logique métier est dans `src/`:

- lecture Excel et configuration: `src/load_excel.py`, `src/config.py`
- sérialisation JSON de config: `src/config_io.py`
- parsing et normalisation: `src/transformations.py`
- calculs de couverture: `src/coverage.py`
- SQL/storage: `src/duckdb_repository.py`
- visualisations Plotly: `src/charts.py`

Si `marimo/data/` est supprimé, relance `ingest.py` avant d'ouvrir `app.py`.
