const entitySpecs = [
  { entityValue: "E1", entityLabel: "Entity 1" },
  { entityValue: "E2", entityLabel: "Entity 2" },
  { entityValue: "E3", entityLabel: "Entity 3" },
  { entityValue: "E4", entityLabel: "Entity 4" },
];

export const defaultConfig = {
  hierarchySheets: [
    {
      sheetName: ["BIAN Capabilities"],
      nodeKind: "businessCapacity",
      // 1-based row number containing the real column headers.
      // Set this to 3 when the first two Excel rows are merged title/comment rows.
      headerRow: 3,
      // The hierarchy sheet is read level by level. Do not use columns that
      // already contain the full path here, otherwise node labels will be wrong.
      pathColumns: [
        ["Business Capability (L1)"],
        ["Business Capability (L2)"],
        ["Business Capability (L3)"],
      ],
      pathCodeColumns: [
        [],
        ["Business Capability (L2) long name"],
        ["Business Capability (L3) long name"],
      ],
    },
  ],
  mappingSheets: [
    ...entitySpecs.map(({ entityValue, entityLabel }) => ({
      sheetName: [`${entityValue}-BCM`],
      applicationCodeColumn: ["Application Code"],
      applicationColumn: ["Application Display Name"],
      applicationNameColumn: ["Application Name"],
      entityValue: entityLabel,
      // BIAN L2 / BIAN L3 contain long path values, for example:
      // "3.1 Enterprise Enabling / Facility and Equipment Management".
      // The loader strips the numeric prefix and splits on " / ".
      targetPathColumns: [
        ["BIAN L2"],
        ["BIAN L3"],
      ],
      defaultTargetKind: "businessCapacity",
    })),
  ],
};

export const demoWorkbookRows = {
  sheets: [
    {
      name: "Business Capabilities",
      headers: ["Domaine", "Réglementation", "Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4"],
      rows: [
        { Domaine: "Sales", "Réglementation": "SOX", "Niveau 1": "Order to Cash", "Niveau 2": "Order Capture", "Niveau 3": "Order Validation", "Niveau 4": "Fraud Check" },
        { Domaine: "Sales", "Réglementation": "SOX", "Niveau 1": "Order to Cash", "Niveau 2": "Order Capture", "Niveau 3": "Order Validation", "Niveau 4": "Credit Check" },
        { Domaine: "Finance", "Réglementation": "IFRS", "Niveau 1": "Record to Report", "Niveau 2": "Close", "Niveau 3": "Ledger", "Niveau 4": "Posting" },
        { Domaine: "Finance", "Réglementation": "IFRS", "Niveau 1": "Record to Report", "Niveau 2": "Close", "Niveau 3": "Ledger", "Niveau 4": "Reconciliation" },
      ],
    },
    {
      name: "Application mappings",
      headers: ["Entité", "Application", "Type de nœud", "Libellé cible", "Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4"],
      rows: [
        { Entité: "Client", Application: "App A", "Type de nœud": "businessCapacity", "Libellé cible": "", "Niveau 1": "Order to Cash", "Niveau 2": "Order Capture", "Niveau 3": "Order Validation", "Niveau 4": "Fraud Check" },
        { Entité: "Client", Application: "App B", "Type de nœud": "businessCapacity", "Libellé cible": "", "Niveau 1": "Order to Cash", "Niveau 2": "Order Capture", "Niveau 3": "Order Validation", "Niveau 4": "" },
        { Entité: "Client", Application: "App B", "Type de nœud": "regulation", "Libellé cible": "SOX", "Niveau 1": "", "Niveau 2": "", "Niveau 3": "", "Niveau 4": "" },
        { Entité: "Finance", Application: "App C", "Type de nœud": "businessCapacity", "Libellé cible": "", "Niveau 1": "Record to Report", "Niveau 2": "Close", "Niveau 3": "Ledger", "Niveau 4": "Posting" },
        { Entité: "Finance", Application: "App D", "Type de nœud": "businessCapacity", "Libellé cible": "", "Niveau 1": "Record to Report", "Niveau 2": "Close", "Niveau 3": "Ledger", "Niveau 4": "" },
      ],
    },
  ],
};
