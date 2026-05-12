import { TypedGraph, normalizeGraphId } from "./graph.js";
import { findSheetByName, matchHeader, normalizeText, stableKey } from "./utils.js";

function readRowValue(row, candidates) {
  const header = matchHeader(Object.keys(row), candidates);
  if (!header) return "";
  return String(row[header] ?? "").trim();
}

function resolveColumns(headers, spec, fields) {
  const resolved = {};
  for (const field of fields) {
    resolved[field] = matchHeader(headers, spec[field]) ?? null;
  }
  return resolved;
}

function splitMappingValues(value) {
  return String(value ?? "")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function rowToHeaders(row) {
  return (row ?? []).map((value) => String(value ?? "").trim());
}

function rowsFromHeaderRow(rawRows, headerRow = 1) {
  const headerIndex = Math.max(0, Number(headerRow || 1) - 1);
  const headers = rowToHeaders(rawRows[headerIndex]);
  const rows = rawRows
    .slice(headerIndex + 1)
    .map((row, index) => ({ row, rowNumber: headerIndex + index + 2 }))
    .filter(({ row }) => row.some((value) => String(value ?? "").trim() !== ""))
    .map(({ row, rowNumber }) => {
      const record = {};
      headers.forEach((header, index) => {
        if (!header) return;
        record[header] = row[index] ?? "";
      });
      Object.defineProperty(record, "__rowNumber", {
        value: rowNumber,
        enumerable: false,
      });
      return record;
    });
  return { headers, rows };
}

function sheetForSpec(sheet, spec) {
  const headerRow = Number(spec.headerRow ?? 1);
  if (headerRow <= 1 || !Array.isArray(sheet.rawRows)) {
    return sheet;
  }
  const parsed = rowsFromHeaderRow(sheet.rawRows, headerRow);
  return {
    ...sheet,
    headers: parsed.headers,
    rows: parsed.rows,
    configuredHeaderRow: headerRow,
  };
}

function formatColumnAliases(columnSpecs) {
  return columnSpecs
    .map((aliases) => aliases.join(" | "))
    .join(", ");
}

function columnName(index) {
  let value = index + 1;
  let name = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    name = String.fromCharCode(65 + remainder) + name;
    value = Math.floor((value - 1) / 26);
  }
  return name;
}

function rowNumber(row, fallback) {
  return Number(row.__rowNumber ?? fallback);
}

function safeCellText(value) {
  try {
    return String(value ?? "").trim();
  } catch (error) {
    return `[unreadable value: ${error instanceof Error ? error.message : String(error)}]`;
  }
}

function rowCellSummary(row, headers, excelRowNumber) {
  const cells = headers
    .map((header, index) => ({ header, index, text: safeCellText(row[header]) }))
    .filter(({ header, text }) => header && text !== "")
    .slice(0, 12)
    .map(({ header, index, text }) => {
      const truncated = text.length > 120 ? `${text.slice(0, 117)}...` : text;
      return `${columnName(index)}${excelRowNumber} ${header}="${truncated}"`;
    });
  return cells.length ? cells.join("; ") : "(no non-empty configured cells)";
}

function wrapRowError(error, { workbookName, sheet, row, rowIndex, phase }) {
  const excelRowNumber = rowNumber(row, rowIndex + 2);
  const cause = error instanceof Error ? error.message : String(error);
  return new Error([
    `Error while ${phase} in workbook "${workbookName}", sheet "${sheet.name}", row ${excelRowNumber}.`,
    `Cells: ${rowCellSummary(row, sheet.headers, excelRowNumber)}.`,
    `Cause: ${cause}`,
  ].join(" "));
}

function parseBusinessCapabilityPath(value) {
  const text = String(value ?? "").trim();
  if (!text) return [];
  const withoutCode = text.replace(/^\d+(?:\.\d+)*\s+/, "").trim();
  if (withoutCode.includes(" / ")) {
    return withoutCode.split(" / ").map((part) => part.trim()).filter(Boolean);
  }
  return [withoutCode];
}

class GraphBuilder {
  constructor(graph) {
    this.graph = graph;
    this.labelIndex = new Map();
    this.pathIndex = new Map();
  }

  indexLabel(kind, label, key) {
    const normalized = normalizeText(label);
    if (!normalized) return;
    if (!this.labelIndex.has(kind)) this.labelIndex.set(kind, new Map());
    const kindMap = this.labelIndex.get(kind);
    if (!kindMap.has(normalized)) {
      kindMap.set(normalized, new Set());
    }
    kindMap.get(normalized).add(key);
  }

  indexPath(kind, pathKey, key) {
    if (!this.pathIndex.has(kind)) this.pathIndex.set(kind, new Map());
    this.pathIndex.get(kind).set(pathKey, key);
  }

  resolveByLabel(kind, label) {
    const kindMap = this.labelIndex.get(kind);
    if (!kindMap) return null;
    const keys = Array.from(kindMap.get(normalizeText(label)) ?? []);
    return keys.length ? keys[0] : null;
  }

  ensureNode(kind, label, meta = {}, pathKey = null) {
    const normalizedLabel = normalizeGraphId(label) || "node";
    const id = pathKey ?? meta.nodeId ?? stableKey([kind, normalizedLabel]);
    const node = this.graph.ensureNode({ kind, id, label, meta });
    this.indexLabel(kind, label, node.key);
    if (pathKey) this.indexPath(kind, pathKey, node.key);
    return node;
  }

  ensureApplication(label, meta = {}) {
    return this.ensureNode("application", label, meta);
  }

  ensureEntity(label, meta = {}) {
    return this.ensureNode("entity", label, meta);
  }

  ensureHierarchyPath(kind, labels, meta = {}, parentKey = null) {
    let currentParentKey = parentKey;
    let cumulativePath = [];
    let currentNode = null;
    for (const label of labels) {
      if (!String(label ?? "").trim()) continue;
      cumulativePath = [...cumulativePath, label];
      const pathKey = stableKey([kind, ...cumulativePath]);
      currentNode = this.graph.getNode(`${kind}:${pathKey}`) ?? this.ensureNode(kind, label, meta, pathKey);
      if (currentParentKey && currentParentKey !== currentNode.key) {
        const exists = this.graph.getOutgoing(currentParentKey, "contains").some((edge) => edge.target === currentNode.key);
        if (!exists) {
          this.graph.addEdge(currentParentKey, currentNode.key, "contains", meta);
        }
      }
      currentParentKey = currentNode.key;
    }
    return currentNode;
  }

  ensureLabelNode(kind, label, meta = {}) {
    const existing = this.resolveByLabel(kind, label);
    if (existing) return this.graph.getNode(existing);
    return this.ensureNode(kind, label, meta);
  }
}

function normalizeNodeKind(value) {
  const text = normalizeText(value);
  if (!text) return "businessCapacity";
  if (text.includes("business") || text.includes("capacity")) return "businessCapacity";
  if (text.includes("domain")) return "domain";
  if (text.includes("regulation") || text.includes("rglmnt")) return "regulation";
  if (text.includes("application") || text === "app") return "application";
  if (text.includes("entity")) return "entity";
  return normalizeGraphId(value) || "node";
}

function ingestHierarchySheet(builder, workbookName, sheet, spec, warnings) {
  const pathColumns = spec.pathColumns ?? [];
  const pathHeaders = pathColumns.map((aliases) => matchHeader(sheet.headers, aliases));
  if (!pathHeaders.some(Boolean)) {
    const headerRowText = sheet.configuredHeaderRow ? ` using headerRow=${sheet.configuredHeaderRow}` : "";
    throw new Error([
      `Sheet "${sheet.name}" in ${workbookName}: no capacity path columns matched${headerRowText}.`,
      `Expected one of: ${formatColumnAliases(pathColumns)}.`,
      `Detected headers: ${sheet.headers.filter(Boolean).join(", ") || "(none)"}.`,
      `If the Excel headers are not on line 1, set "headerRow" on this hierarchy sheet in config.js.`,
    ].join(" "));
  }

  for (const [rowIndex, row] of sheet.rows.entries()) {
    try {
      const excelRowNumber = rowNumber(row, rowIndex + 2);
      const meta = { sourceWorkbook: workbookName, sourceSheet: sheet.name, rowIndex: excelRowNumber };
      const pathValues = pathHeaders.map((header) => (header ? String(row[header] ?? "").trim() : "")).filter(Boolean);
      if (pathValues.length) {
        builder.ensureHierarchyPath(spec.nodeKind ?? "businessCapacity", pathValues, meta);
      }
    } catch (error) {
      throw wrapRowError(error, { workbookName, sheet, row, rowIndex, phase: "ingesting hierarchy row" });
    }
  }
}

function targetNodesFromRow(builder, row, spec, meta, warnings) {
  const kindHeader = spec.targetKindColumn ? matchHeader(Object.keys(row), spec.targetKindColumn) : null;
  const labelHeader = spec.targetLabelColumn ? matchHeader(Object.keys(row), spec.targetLabelColumn) : null;
  const pathHeaders = (spec.targetPathColumns ?? []).map((aliases) => matchHeader(Object.keys(row), aliases));
  const rawKind = kindHeader ? String(row[kindHeader] ?? "").trim() : "";
  const kind = normalizeNodeKind(rawKind || spec.defaultTargetKind || "businessCapacity");
  const label = labelHeader ? String(row[labelHeader] ?? "").trim() : "";
  const pathValues = pathHeaders.flatMap((header) => (header ? splitMappingValues(row[header]) : []));

  if (kind === "businessCapacity" && pathValues.length) {
    return pathValues
      .map((value) => parseBusinessCapabilityPath(value))
      .filter((path) => path.length)
      .map((path) => builder.ensureHierarchyPath("businessCapacity", path, meta, null));
  }

  if ((kind === "domain" || kind === "regulation" || kind === "application" || kind === "entity") && label) {
    return [builder.ensureLabelNode(kind, label, meta)];
  }

  if (pathValues.length) {
    return pathValues
      .map((value) => parseBusinessCapabilityPath(value))
      .filter((path) => path.length)
      .map((path) => builder.ensureHierarchyPath(kind, path, meta, null));
  }

  if (label) {
    return [builder.ensureLabelNode(kind, label, meta)];
  }

  warnings.push(`Row ${meta.rowIndex} in ${meta.sourceSheet} has no resolvable target node.`);
  return [];
}

function ingestMappingSheet(builder, workbookName, sheet, spec, warnings) {
  const applicationCodeHeader = spec.applicationCodeColumn ? matchHeader(sheet.headers, spec.applicationCodeColumn) : null;
  const applicationNameHeader = spec.applicationNameColumn ? matchHeader(sheet.headers, spec.applicationNameColumn) : null;
  const applicationHeader = matchHeader(sheet.headers, spec.applicationColumn);
  const entityHeader = spec.entityColumn ? matchHeader(sheet.headers, spec.entityColumn) : null;
  if (!applicationHeader && !applicationCodeHeader) {
    warnings.push(`Sheet "${sheet.name}" in ${workbookName}: application column not found.`);
    return;
  }

  for (const [rowIndex, row] of sheet.rows.entries()) {
    try {
      const excelRowNumber = rowNumber(row, rowIndex + 2);
      const meta = { sourceWorkbook: workbookName, sourceSheet: sheet.name, rowIndex: excelRowNumber };
      const applicationCode = applicationCodeHeader ? String(row[applicationCodeHeader] ?? "").trim() : "";
      const applicationName = applicationNameHeader ? String(row[applicationNameHeader] ?? "").trim() : "";
      let applicationLabel = applicationHeader ? String(row[applicationHeader] ?? "").trim() : "";
      if (!applicationLabel && applicationName) applicationLabel = applicationName;
      if (!applicationLabel && applicationCode) applicationLabel = applicationCode;
      if (!applicationLabel && !applicationCode) continue;

      const entityLabel = spec.entityValue ? String(spec.entityValue).trim() : (entityHeader ? String(row[entityHeader] ?? "").trim() : "");
      const appNode = builder.ensureApplication(applicationLabel || applicationCode, {
        ...meta,
        nodeId: applicationCode || applicationLabel,
        entity: entityLabel,
        applicationCode,
        applicationName,
      });

      if (entityLabel) {
        const entityNode = builder.ensureEntity(entityLabel, meta);
        const existing = builder.graph.getOutgoing(appNode.key, "belongs_to").some((edge) => edge.target === entityNode.key);
        if (!existing) builder.graph.addEdge(appNode.key, entityNode.key, "belongs_to", meta);
      }

      for (const targetNode of targetNodesFromRow(builder, row, spec, meta, warnings)) {
        const existing = builder.graph.getOutgoing(appNode.key, "mapped_to").some((edge) => edge.target === targetNode.key);
        if (!existing) builder.graph.addEdge(appNode.key, targetNode.key, "mapped_to", meta);
      }
    } catch (error) {
      throw wrapRowError(error, { workbookName, sheet, row, rowIndex, phase: "ingesting mapping row" });
    }
  }
}

export function buildGraphFromWorkbooks(workbooks, config) {
  const graph = new TypedGraph();
  const builder = new GraphBuilder(graph);
  const warnings = [];

  for (const workbook of workbooks) {
    for (const sheet of workbook.sheets) {
      for (const spec of config.hierarchySheets ?? []) {
        if (findSheetByName({ sheets: [sheet] }, spec.sheetName)) {
          ingestHierarchySheet(builder, workbook.name, sheetForSpec(sheet, spec), spec, warnings);
        }
      }
      for (const spec of config.mappingSheets ?? []) {
        if (findSheetByName({ sheets: [sheet] }, spec.sheetName)) {
          ingestMappingSheet(builder, workbook.name, sheetForSpec(sheet, spec), spec, warnings);
        }
      }
    }
  }

  return { graph, warnings, summary: graph.summary() };
}

export function normalizeWorkbooks(parsedWorkbooks) {
  return parsedWorkbooks.map((workbook) => ({
    name: workbook.name,
    sheets: workbook.sheets.map((sheet) => ({
      name: sheet.name,
      headers: sheet.headers,
      rows: sheet.rows,
      rawRows: sheet.rawRows,
    })),
  }));
}

export function summarizeWorkbooks(workbooks) {
  return workbooks.map((workbook) => ({
    name: workbook.name,
    sheets: workbook.sheets.map((sheet) => ({
      name: sheet.name,
      rowCount: sheet.rows.length,
      headers: sheet.headers,
    })),
  }));
}
