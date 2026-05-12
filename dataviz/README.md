# Dataviz Angular

Dashboard Angular autonome pour exploiter le fichier compact `storage-data.json` produit par `load-data/`.

## Rôle

- Charger automatiquement `src/assets/storage-data.json`.
- Permettre un fallback par sélection manuelle d’un fichier JSON.
- Reconstruire le graphe typé en mémoire.
- Calculer les candidats de couverture applicative côté client.
- Afficher un dashboard v1 avec filtres, seuils et détail explicatif.

`load-data/` reste responsable de l’import Excel et de l’export JSON. Cette app ne lit pas directement les fichiers Excel.

## Commandes

```bash
pnpm install
pnpm test
pnpm build
pnpm ng serve --port 4201 --host 127.0.0.1
```

## Données

Le fichier de démonstration attendu est:

```text
src/assets/storage-data.json
```

Depuis le dashboard, il est aussi possible de charger un autre JSON local via le sélecteur de fichier.

## Structure

- `src/app/models/storage-data.ts`: types du JSON compact, graphe typé et candidats.
- `src/app/models/treemap-data.ts`: contrat de données pour les treemaps.
- `src/app/services/storage-loader.service.ts`: chargement du JSON par asset ou fichier local.
- `src/app/services/graph.service.ts`: reconstruction du graphe, index et fermeture hiérarchique.
- `src/app/services/coverage-analysis.service.ts`: calcul des candidats exacts et partiels.
- `src/app/visualizations/treemap-layout.ts`: calcul D3 pur du layout treemap, sans dépendance Angular.
- `src/app/components/business-domain-treemap`: composant SVG/D3 pour afficher une métrique hiérarchique par domaine.
- `src/testing/fixtures`: jeux de données compacts pour les tests.

## Treemap Business Domain

Le composant `app-business-domain-treemap` affiche un treemap SVG basé sur D3. Il ne calcule pas lui-même la métrique métier: il reçoit une hiérarchie déjà agrégée.

Le layout D3 est isolé dans `src/app/visualizations/treemap-layout.ts`. Ce fichier transforme `TreemapData` en tuiles positionnées (`TreemapTile[]`). Le composant Angular ne fait ensuite que rendre ces tuiles en SVG. Ce pattern doit être réutilisé pour les futurs diagrammes Sankey, chord, tree ou matrix:

```text
models/*-data.ts           -> contrat d'entrée
visualizations/*-layout.ts -> calcul D3 pur et testable
components/*               -> rendu Angular/SVG et interactions
```

Usage Angular:

```html
<app-business-domain-treemap
  [data]="businessDomainTreemapData"
  [width]="980"
  [height]="520"
/>
```

Format TypeScript attendu:

```ts
interface TreemapData {
  label: string;
  metric: {
    key: string;
    label: string;
    unit?: string;
  };
  children: TreemapNode[];
}

interface TreemapNode {
  id: string;
  label: string;
  value?: number;
  children?: TreemapNode[];
  meta?: Record<string, unknown>;
}
```

Règles:

- `children` représente la hiérarchie affichée, par exemple domaine -> sous-domaine -> segment.
- `value` est la métrique numérique à visualiser.
- Si un nœud a des enfants, la surface affichée correspond à la somme des valeurs des feuilles descendantes.
- `metric.key` identifie la métrique technique, par exemple `applicationCount`, `tco`, `riskScore`.
- `metric.label` est le libellé affiché, par exemple `Applications`, `TCO`, `Risque`.
- `metric.unit` est optionnel, par exemple `EUR`, `kEUR`, `%`.
- `meta` permet de transporter des informations métier non affichées par défaut.

Exemple pour un nombre d’applications par business domain:

```ts
const businessDomainTreemapData: TreemapData = {
  label: 'Business domains',
  metric: {
    key: 'applicationCount',
    label: 'Applications',
  },
  children: [
    {
      id: 'retail',
      label: 'Retail Banking',
      children: [
        { id: 'retail-payments', label: 'Payments', value: 42 },
        { id: 'retail-lending', label: 'Lending', value: 31 },
      ],
    },
    {
      id: 'wealth',
      label: 'Wealth Management',
      value: 18,
    },
  ],
};
```

Exemple pour un TCO par business domain:

```ts
const tcoTreemapData: TreemapData = {
  label: 'Business domains',
  metric: {
    key: 'tco',
    label: 'TCO',
    unit: 'kEUR',
  },
  children: [
    {
      id: 'retail',
      label: 'Retail Banking',
      children: [
        { id: 'retail-payments', label: 'Payments', value: 1250 },
        { id: 'retail-lending', label: 'Lending', value: 980 },
      ],
    },
  ],
};
```

Le composant est volontairement indépendant du graphe. La prochaine étape sera d’ajouter un service d’agrégation qui transforme le `TypedGraph` en `TreemapData`.

## Tests

Les tests unitaires couvrent:

- reconstruction des nœuds et arêtes;
- fermeture descendante via `contains`;
- couverture L2 vers L3;
- seuils de couverture;
- isolation par entité;
- rendu minimal du dashboard;
- rendu du treemap et calcul du total.
