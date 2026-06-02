# Marimo exploration dataviz

Prototype Python/Marimo pour explorer les mappings applicatifs.

## Arborescence

- `notebooks/reports/` contient les notebooks d'exploitation
- `notebooks/admin/` contient les notebooks de chargement, debug et paramétrage
- `src/report_helpers/` contient les helpers réutilisés par les notebooks

L'ingestion Excel est séparée des rapports:

- `notebooks/admin/ingest.py` charge l'Excel et réécrit `data/local.duckdb`
- `notebooks/reports/app.py` lit uniquement les tables DuckDB présentes dans `data/`
- `notebooks/reports/coverage.py` liste les candidats de couverture applicative et détaille les applications couvrantes
- `notebooks/reports/treemap.py` affiche un treemap des capacités métiers par applications ou incidents
- `notebooks/admin/config_builder.py` sert à éditer et sauvegarder le JSON de paramétrage dans Marimo

## Installation

```bash
cd marimo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
marimo run notebooks/admin/ingest.py
```

Puis:

```bash
marimo run notebooks/reports/app.py
```

## Export pour Windows

Pour déposer un bundle exécutable sur un partage SharePoint ou un répertoire externe:

```bash
bash scripts/export_for_windows.sh "/chemin/vers/le/sharepoint"
```

Le script copie:

- `data/`
- `src/`
- `notebooks/`
- `README.md`
- `requirements.txt`

## Lancement sous Windows

Depuis PowerShell, dans le répertoire copié:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
marimo run notebooks\\reports\\app.py
```

Si PowerShell bloque l'activation du venv:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Pour les autres notebooks de reporting:

```powershell
marimo run notebooks\\reports\\treemap.py
marimo run notebooks\\reports\\sankey.py
marimo run notebooks\\reports\\sankey_hierarchy.py
```

Pour les notebooks d’administration:

```powershell
marimo run notebooks\\admin\\ingest.py
marimo run notebooks\\admin\\debug_duckdb.py
marimo run notebooks\\admin\\config_builder.py
```

Pour un contrôle non interactif:

```bash
python notebooks/admin/ingest.py
python notebooks/reports/app.py
python -m unittest discover -s tests
```

## Stockage

La cible est un simple fichier DuckDB local:

- `marimo/data/local.duckdb`

Le répertoire `marimo/data/` contient aussi les fichiers temporaires éventuellement créés par l’ingestion.

## Tables DuckDB

Les notebooks de reporting lisent les tables suivantes dans `data/local.duckdb`:

- `dim_business_capability`: hiérarchie des capacités métiers, avec `code`, `level`, `label`, `long_name`, `parent_code` et les chemins `path_l1` à `path_l5`
- `dim_application`: référentiel des applications, avec `application_code`, `application_name`, `display_name`, `entity_code`
- `dim_entity`: référentiel des entités
- `bridge_application_capability`: mappings application -> capacité
- `capability_closure`: fermeture hiérarchique des capacités, utile pour les agrégations et les calculs de couverture
- `import_warnings`: warnings ou erreurs rencontrés pendant l’import
- `fact_incidents` si la source incidents est présente dans la configuration

Les notebooks n’accèdent pas directement à Excel une fois le cache DuckDB écrit.

## Principe

Les cellules Marimo restent fines. La logique métier est dans `src/`:

- lecture Excel et configuration: `src/load_excel.py`, `src/config.py`
- sérialisation JSON de config: `src/config_io.py`
- parsing et normalisation: `src/transformations.py`
- calculs de couverture: `src/coverage.py`
- SQL/storage: `src/duckdb_repository.py`
- visualisations Plotly: `src/charts.py`

Si `data/` est supprimé, relance `notebooks/admin/ingest.py` avant d'ouvrir les notebooks de reporting.
