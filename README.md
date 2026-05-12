# Graphe de couverture applicative

Application de couverture applicative avec deux parties séparées:

- `load-data/index.html` pour importer les classeurs Excel, construire le graphe typé et exporter `storage-data.json`
- `dataviz/` pour relire `storage-data.json`, recalculer les candidats côté client et afficher le dashboard Angular

## Utilisation

1. Ouvrir `load-data/index.html` dans un navigateur moderne.
2. Charger un ou plusieurs fichiers Excel (`.xlsx`).
3. Adapter la configuration JSON si vos onglets ou colonnes diffèrent du modèle par défaut.
4. Lancer l’import puis exporter `storage-data.json`.
5. Copier ou déposer ce fichier dans `dataviz/src/assets/storage-data.json`, ou le charger manuellement depuis le dashboard.
6. Lancer la dataviz Angular:

```bash
cd dataviz
pnpm install
pnpm ng serve --port 4201 --host 127.0.0.1
```

La page est ensuite disponible sur `http://127.0.0.1:4201/`.

Si ton navigateur bloque le chargement relatif du JSON en ouvrant le fichier directement en `file://`, ouvre le dossier via un petit serveur local ou sélectionne manuellement `storage-data.json` dans la page de viz.

## Modèle attendu

- Un onglet de hiérarchie de capacités métiers avec jusqu’à 4 niveaux.
- Un ou plusieurs onglets de mapping application -> nœud cible.
- Les cibles peuvent être des capacités métiers, des domaines ou des réglementations.
- Un onglet `Applicability Taxonomy` multi-axes pour la régulation, les segments clients, les produits, les canaux, la géographie et les domaines.
- La dataviz Angular relit un JSON intermédiaire et recalcule les candidats en mémoire.

## Sorties

- Résumé du graphe en mémoire dans la page d’ingestion.
- Export `storage-data.json` compact depuis `load-data/index.html`.
- Les seuils, candidats et visualisations sont calculés côté `dataviz/`.

## Mettre à jour `load-data/src/config.js` a un Agent / LLM

Quand tu veux accélérer le mapping sur une feuille Excel réelle, le plus efficace est de donner à Agent / LLM le rôle de “traducteur de schéma” entre ton classeur et `load-data/src/config.js`.

### Ce qu’il faut lui fournir

- Le nom exact des onglets source.
- Les colonnes exactes pour:
  - les 4 niveaux de capacités métiers,
  - l’entité,
  - l’application,
  - le type de nœud cible si tu en utilises plusieurs,
  - le libellé cible si la cible n’est pas portée par les niveaux.
- Les variantes de libellés à anticiper:
  - accents ou non,
  - singulier / pluriel,
  - français / anglais,
  - `Level 1` vs `Niveau 1`, etc.

### Comment demander à Agent / LLM de modifier `load-data/src/config.js`

Tu peux lui demander quelque chose comme:

> "Lis le classeur Excel joint. Mets à jour `load-data/src/config.js` pour que `hierarchySheets` pointe vers les bons onglets de capacités et que `mappingSheets` reflète les bons onglets de mapping application -> capacité. Conserve un schéma semi-configuré avec des alias de colonnes, mais remplace les noms génériques par les noms réels du fichier."

### Ce que Agent / LLM doit ajuster dans `load-data/src/config.js`

- `hierarchySheets[*].sheetName`
  - noms d’onglets contenant la hiérarchie des capacités.
- `hierarchySheets[*].headerRow`
  - numéro de ligne Excel, base 1, qui contient les vrais en-têtes.
  - utiliser `3` si les deux premières lignes sont des titres/commentaires fusionnés.
- `hierarchySheets[*].pathColumns`
  - alias des 4 niveaux de capacité, dans l’ordre réel de ton modèle.
- `mappingSheets[*].sheetName`
  - onglets qui portent les mappings applicatifs.
- `mappingSheets[*].headerRow`
  - optionnel, même principe que pour `hierarchySheets`; utile si les en-têtes ne sont pas en ligne 1.
- `mappingSheets[*].applicationColumn`
  - colonne qui identifie l’application.
- `mappingSheets[*].entityColumn`
  - colonne qui identifie l’entité.
- `mappingSheets[*].targetKindColumn`
  - colonne qui dit si la cible est une capacité, un domaine, une réglementation, etc.
- `mappingSheets[*].targetLabelColumn`
  - colonne du libellé cible si tu n’utilises pas les 4 niveaux.
- `mappingSheets[*].targetPathColumns`
  - alias des colonnes si la cible est exprimée sous forme de chemin hiérarchique.

### Bon réflexe de validation

Après modification de `load-data/src/config.js`:

1. Ouvre `load-data/index.html`.
2. Charge la démo pour vérifier que la page reste fonctionnelle.
3. Charge ton vrai classeur.
4. Vérifie que:
   - les bons onglets sont détectés,
   - les bons candidats apparaissent,
   - le détail d’un candidat explique bien la couverture.

Si le mapping est faux, le premier endroit à corriger est `load-data/src/config.js`, pas le moteur de graphe.

### Exemple avec en-têtes Excel en ligne 3

Si un onglet commence par deux lignes de titre fusionnées et que les vrais noms de colonnes sont en ligne 3:

```js
{
  sheetName: ["BIAN Capabilities"],
  nodeKind: "businessCapacity",
  headerRow: 3,
  pathColumns: [
    ["Business Capability (L1)"],
    ["Business Capability (L2)"],
    ["Business Capability (L3)"],
  ],
}
```

Si les colonnes attendues ne sont pas trouvées, l’import échoue maintenant explicitement avec les en-têtes détectés et les colonnes attendues.
