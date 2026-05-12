# AGENTS.md - Guidelines for this project

## Commits
- Tous les commits doivent utiliser un message conforme à Conventional Commits.
- Utiliser un préfixe adapté au changement: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

## Project rules
- Préférer une interface simple, exécutable localement sans dépendances lourdes quand c’est possible.
- Garder la configuration métier d’ingestion dans `load-data/src/config.js`.
- Garder la logique de graphe et d’analyse séparée de l’UI.
- Éviter d’introduire une nouvelle dépendance sans bénéfice clair sur le parsing Excel, le graphe ou la visualisation.

## File handling
- Ne pas renommer ou supprimer les fichiers sans raison fonctionnelle.
- Conserver les chemins et noms de fichiers stables lorsque cela simplifie l’usage par un non-développeur.
