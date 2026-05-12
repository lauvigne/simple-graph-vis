export const defaultConfig = {
  hierarchySheets: [
    {
      sheetName: ["BIAN Capabilities"],
      nodeKind: "businessCapacity",
      pathColumns: [
        ["Business Capability (L1)"],
        ["Business Capability (L2)"],
        ["Business Capability (L3)"],
      ],
    },
  ],
  mappingSheets: [
    {
      sheetName: ["E1-BCM"],
      applicationCodeColumn: ["Application Code"],
      applicationColumn: ["Application Display Name"],
      applicationNameColumn: ["Application Name"],
      entityValue: "E1",
      targetKindColumn: ["Type de nœud", "Node kind", "Type", "Target kind"],
      targetLabelColumn: ["Libellé cible", "Target label", "Target", "Node"],
      targetPathColumns: [
        ["BIAN L2"],
        ["BIAN L3"],
      ],
      defaultTargetKind: "businessCapacity",
    },
    {
      sheetName: ["E2-BCM"],
      applicationCodeColumn: ["Application Code"],
      applicationColumn: ["Application Display Name"],
      applicationNameColumn: ["Application Name"],
      entityValue: "E2",
      targetPathColumns: [
        ["BIAN L2"],
        ["BIAN L3"],
      ],
      defaultTargetKind: "businessCapacity",
    },
    {
      sheetName: ["E3-BCM"],
      applicationCodeColumn: ["Application Code"],
      applicationColumn: ["Application Display Name"],
      applicationNameColumn: ["Application Name"],
      entityValue: "E3",
      targetPathColumns: [
        ["BIAN L2"],
        ["BIAN L3"],
      ],
      defaultTargetKind: "businessCapacity",
    },
    {
      sheetName: ["E4-BCM"],
      applicationCodeColumn: ["Application Code"],
      applicationColumn: ["Application Display Name"],
      applicationNameColumn: ["Application Name"],
      entityValue: "E4",
      targetPathColumns: [
        ["BIAN L2"],
        ["BIAN L3"],
      ],
      defaultTargetKind: "businessCapacity",
    },
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
