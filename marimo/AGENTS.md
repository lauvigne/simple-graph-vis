# AGENTS.md - marimo

## Contexte important
- Les notebooks Marimo doivent rester fins: ils chargent des données via `src/duckdb_repository.py` puis affichent les rapports.
- `src/sample_data.py` est réservé aux tests et fixtures de test. Les notebooks ne doivent pas l'importer.
- Le stockage local est DuckDB simple, dans `marimo/data/local.duckdb`.
- La logique métier vit dans `src/` et `reports/`, pas dans les cellules Marimo.

## Règles de travail
- Préférer des notebooks autonomes et lisibles, avec peu de logique inline.
- Éviter d'introduire de nouvelles dépendances sans bénéfice clair.
- Garder les chemins et les noms de fichiers stables quand c'est possible.
- Si un notebook a besoin d'un état vide, utiliser les helpers de `src/` plutôt que `sample_data.py`.

