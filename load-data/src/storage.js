import { TypedGraph } from "./graph.js";

function compactMeta(node) {
  if (node.kind !== "application") return undefined;
  const meta = node.meta ?? {};
  const compact = {};
  if (meta.applicationCode) compact.applicationCode = meta.applicationCode;
  if (meta.applicationName) compact.applicationName = meta.applicationName;
  if (meta.entity) compact.entity = meta.entity;
  return Object.keys(compact).length ? compact : undefined;
}

function serializeNode(node) {
  const serialized = {
    k: node.key,
    i: node.id,
    t: node.kind,
    l: node.label,
  };
  const meta = compactMeta(node);
  if (meta) serialized.m = meta;
  return serialized;
}

function serializeEdge(edge) {
  return {
    s: edge.source,
    t: edge.target,
    r: edge.type,
  };
}

function summarizeWorkbook(workbook) {
  return {
    name: workbook.name,
    sheets: Array.from(workbook.sheets ?? []).map((sheet) => ({
      name: sheet.name,
      headers: Array.from(sheet.headers ?? []),
      rowCount: sheet.rows?.length ?? sheet.rowCount ?? 0,
    })),
  };
}

export function createStorageData({
  config,
  workbooks = [],
  graph,
  warnings = [],
}) {
  const serializedGraph = {
    summary: graph.summary(),
    nodes: Array.from(graph.nodes.values()).map(serializeNode),
    edges: Array.from(graph.edges).map(serializeEdge),
  };

  return {
    version: "2.0",
    format: "compact-graph",
    generatedAt: new Date().toISOString(),
    configSnapshot: JSON.parse(JSON.stringify(config ?? {})),
    sources: workbooks.map(summarizeWorkbook),
    warnings: Array.from(warnings),
    summary: {
      workbooks: workbooks.length,
      sheets: workbooks.reduce((sum, workbook) => sum + (workbook.sheets?.length ?? 0), 0),
      graph: serializedGraph.summary,
    },
    graph: serializedGraph,
  };
}

export function normalizeStorageData(storageData) {
  const data = storageData ?? {};
  const sources = Array.isArray(data.sources) ? data.sources : data.workbooks;
  return {
    version: data.version ?? "1.0",
    format: data.format ?? "legacy",
    generatedAt: data.generatedAt ?? null,
    configSnapshot: data.configSnapshot ?? {},
    workbooks: Array.isArray(sources) ? sources : [],
    warnings: Array.isArray(data.warnings) ? data.warnings : [],
    summary: data.summary ?? {},
    graph: {
      summary: data.graph?.summary ?? { nodes: 0, edges: 0, kinds: {} },
      nodes: Array.isArray(data.graph?.nodes) ? data.graph.nodes : [],
      edges: Array.isArray(data.graph?.edges) ? data.graph.edges : [],
    },
  };
}

export function buildGraphFromStorage(storageGraph) {
  const graph = new TypedGraph();
  for (const node of Array.isArray(storageGraph?.nodes) ? storageGraph.nodes : []) {
    const kind = node.kind ?? node.t;
    const id = node.id ?? node.i ?? node.key?.split(":").slice(1).join(":") ?? node.k?.split(":").slice(1).join(":") ?? node.label ?? node.l;
    const label = node.label ?? node.l;
    graph.ensureNode({
      kind,
      id,
      label,
      meta: node.meta ?? node.m ?? {},
    });
  }
  for (const edge of Array.isArray(storageGraph?.edges) ? storageGraph.edges : []) {
    graph.addEdge(edge.source ?? edge.s, edge.target ?? edge.t, edge.type ?? edge.r, edge.meta ?? {});
  }
  return graph;
}
