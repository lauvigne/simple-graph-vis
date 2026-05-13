import { TypedGraph, normalizeGraphId } from "./graph.js";
import { findSheetByName, matchHeader, normalizeText, stableKey } from "./utils.js";

function splitCellValues(value, codeDepth = null) {
  if (codeDepth) {
    const values = splitCellValuesByCode(value, codeDepth);
    if (values.length) return values;
  }
  return String(value ?? "")
    .split(",")
    .map((part) => cleanCellText(part))
    .filter(Boolean);
}

function splitCellValuesByCode(value, codeDepth) {
  const text = cleanCellText(value);
  if (!text) return [];
  const codePattern = codeDepth === 2
    ? "\\d+\\.\\d+"
    : `\\d+\\.\\d+(?:\\.\\d+){${codeDepth - 2}}`;
  const regex = new RegExp(`(^|[^\\d.])(${codePattern})(?![\\d.])`, "g");
  const matches = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    matches.push({
      index: match.index + match[1].length,
      code: match[2],
    });
  }
  if (!matches.length) return [];
  return matches
    .map((current, index) => {
      const next = matches[index + 1];
      return cleanCellText(text.slice(current.index, next?.index ?? text.length)
        .replace(/^[,;\s]+/, "")
        .replace(/[,;\s]+$/, ""));
    })
    .filter(Boolean);
}

function expectedBusinessCapabilityCodeDepth(header, aliases) {
  const candidates = [header, ...(Array.isArray(aliases) ? aliases.flat() : [aliases])]
    .map((value) => normalizeText(value));
  if (candidates.some((value) => /\b(?:l3|level 3|niveau 3)\b/.test(value))) return 3;
  if (candidates.some((value) => /\b(?:l2|level 2|niveau 2)\b/.test(value))) return 2;
  return null;
}

function cleanCellText(value) {
  return String(value ?? "")
    .replace(/\s+/g, " ")
    .trim();
}

function stripLeadingCapabilityCode(value) {
  return cleanCellText(value).replace(/^\d+(?:\.\d+)*\s*(?:-\s*)?/, "").trim();
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

function extractLeadingCode(value) {
  const text = cleanCellText(value);
  return text.match(/^(\d+(?:\.\d+)*)\s*(?:-|\s|$)/)?.[1] ?? "";
}

function codeAtLevel(code, levelIndex) {
  const parts = String(code ?? "").split(".").filter(Boolean);
  if (!parts.length || parts.length <= levelIndex) return "";
  return parts.slice(0, levelIndex + 1).join(".");
}

function pathEntriesFromLabels(labels, deepestCode = "") {
  return labels.map((label, index) => ({
    label: cleanCellText(label),
    code: codeAtLevel(deepestCode, index),
  }));
}

function parseBusinessCapabilityPath(value) {
  const text = cleanCellText(value);
  if (!text) return [];
  const code = extractLeadingCode(text);
  const withoutCode = stripLeadingCapabilityCode(text);
  const labels = withoutCode.includes("/")
    ? withoutCode.split(/\s*\/\s*/).map((part) => cleanCellText(part)).filter(Boolean)
    : [withoutCode];
  return pathEntriesFromLabels(labels, code);
}

function normalizePathEntry(value) {
  if (typeof value === "object" && value !== null) {
    return {
      label: cleanCellText(value.label),
      code: cleanCellText(value.code),
    };
  }
  return {
    label: cleanCellText(value),
    code: "",
  };
}

function deepestCodeForRow(row, codeHeaders) {
  for (let index = codeHeaders.length - 1; index >= 0; index--) {
    const header = codeHeaders[index];
    if (!header) continue;
    const code = extractLeadingCode(row[header]);
    if (code) return code;
  }
  return "";
}

function parseBusinessCapabilityPathLegacy(value) {
  const text = cleanCellText(value);
  if (!text) return [];
  const withoutCode = stripLeadingCapabilityCode(text);
  if (withoutCode.includes("/")) {
    return withoutCode.split(/\s*\/\s*/).map((part) => cleanCellText(part)).filter(Boolean);
  }
  return [withoutCode];
}

function parsePathForKind(kind, value) {
  return kind === "businessCapacity"
    ? parseBusinessCapabilityPath(value)
    : parseBusinessCapabilityPathLegacy(value);
}

function resolveTargetPathSpecs(headers, targetPathColumns = []) {
  return targetPathColumns.map((aliases) => {
    const header = matchHeader(headers, aliases);
    return {
      aliases,
      header,
      codeDepth: expectedBusinessCapabilityCodeDepth(header, aliases),
    };
  });
}

function targetPathValues(row, kind, pathSpecs) {
  return pathSpecs.flatMap(({ header, codeDepth }) => {
    if (!header) return [];
    return splitCellValues(row[header], kind === "businessCapacity" ? codeDepth : null);
  });
}

class GraphBuilder {
  constructor(graph) {
    this.graph = graph;
    this.labelIndex = new Map();
    this.pathIndex = new Map();
    this.codeIndex = new Map();
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

  indexCode(kind, code, key) {
    const normalizedCode = cleanCellText(code);
    if (!normalizedCode) return;
    if (!this.codeIndex.has(kind)) this.codeIndex.set(kind, new Map());
    this.codeIndex.get(kind).set(normalizedCode, key);
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
    for (const value of labels) {
      const entry = normalizePathEntry(value);
      if (!entry.label) continue;
      cumulativePath = [...cumulativePath, entry.label];
      const pathKey = stableKey([kind, ...cumulativePath]);
      const nodeMeta = entry.code ? { ...meta, code: entry.code } : meta;
      currentNode = this.graph.getNode(`${kind}:${pathKey}`) ?? this.ensureNode(kind, entry.label, nodeMeta, pathKey);
      if (currentNode && entry.code && currentNode.meta?.code !== entry.code) {
        currentNode.meta = { ...currentNode.meta, code: entry.code };
      }
      if (entry.code) this.indexCode(kind, entry.code, currentNode.key);
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

  resolveHierarchyPath(kind, labels) {
    const entries = labels.map((value) => normalizePathEntry(value)).filter((entry) => entry.label);
    const deepestCode = [...entries].reverse().find((entry) => entry.code)?.code;
    if (deepestCode) {
      const byCode = this.codeIndex.get(kind)?.get(deepestCode);
      if (byCode) return this.graph.getNode(byCode);
    }
    const pathKey = stableKey([kind, ...entries.map((entry) => entry.label)]);
    const byPath = this.pathIndex.get(kind)?.get(pathKey);
    return byPath ? this.graph.getNode(byPath) : null;
  }

  ensureValidatedBusinessCapabilityPath(labels, meta, warnings) {
    const existing = this.resolveHierarchyPath("businessCapacity", labels);
    if (existing) return existing;
    const formatted = labels.map((value) => normalizePathEntry(value).label).filter(Boolean).join(" / ");
    warnings.push([
      `Row ${meta.rowIndex} in ${meta.sourceSheet}: business capability mapping not found in hierarchySheets.`,
      `Value: "${formatted}".`,
      `A new node was created from mapping data; check separators, code, and labels.`,
    ].join(" "));
    return this.ensureHierarchyPath("businessCapacity", labels, meta, null);
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
  const codeHeaders = (spec.pathCodeColumns ?? []).map((aliases) => matchHeader(sheet.headers, aliases));
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
      const pathValues = pathHeaders.map((header) => (header ? cleanCellText(row[header]) : "")).filter(Boolean);
      const deepestCode = deepestCodeForRow(row, codeHeaders);
      if (pathValues.length) {
        builder.ensureHierarchyPath(spec.nodeKind ?? "businessCapacity", pathEntriesFromLabels(pathValues, deepestCode), meta);
      }
    } catch (error) {
      throw wrapRowError(error, { workbookName, sheet, row, rowIndex, phase: "ingesting hierarchy row" });
    }
  }
}

function targetNodesFromRow(builder, row, spec, meta, warnings) {
  const kindHeader = spec.targetKindColumn ? matchHeader(Object.keys(row), spec.targetKindColumn) : null;
  const labelHeader = spec.targetLabelColumn ? matchHeader(Object.keys(row), spec.targetLabelColumn) : null;
  const rawKind = kindHeader ? cleanCellText(row[kindHeader]) : "";
  const kind = normalizeNodeKind(rawKind || spec.defaultTargetKind || "businessCapacity");
  const label = labelHeader ? cleanCellText(row[labelHeader]) : "";
  const pathSpecs = resolveTargetPathSpecs(Object.keys(row), spec.targetPathColumns ?? []);
  const pathValues = targetPathValues(row, kind, pathSpecs);

  if (pathValues.length) {
    return pathValues
      .map((value) => parsePathForKind(kind, value))
      .filter((path) => path.length)
      .map((path) => kind === "businessCapacity"
        ? builder.ensureValidatedBusinessCapabilityPath(path, meta, warnings)
        : builder.ensureHierarchyPath(kind, path, meta, null));
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
      const applicationCode = applicationCodeHeader ? cleanCellText(row[applicationCodeHeader]) : "";
      const applicationName = applicationNameHeader ? cleanCellText(row[applicationNameHeader]) : "";
      let applicationLabel = applicationHeader ? cleanCellText(row[applicationHeader]) : "";
      if (!applicationLabel && applicationName) applicationLabel = applicationName;
      if (!applicationLabel && applicationCode) applicationLabel = applicationCode;
      if (!applicationLabel && !applicationCode) continue;

      const entityLabel = spec.entityValue ? cleanCellText(spec.entityValue) : (entityHeader ? cleanCellText(row[entityHeader]) : "");
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

function ingestConfiguredSheets(workbooks, specs, ingestSheet) {
  for (const workbook of workbooks) {
    for (const sheet of workbook.sheets) {
      for (const spec of specs ?? []) {
        if (findSheetByName({ sheets: [sheet] }, spec.sheetName)) {
          ingestSheet(workbook.name, sheetForSpec(sheet, spec), spec);
        }
      }
    }
  }
}

export function buildGraphFromWorkbooks(workbooks, config) {
  const graph = new TypedGraph();
  const builder = new GraphBuilder(graph);
  const warnings = [];

  ingestConfiguredSheets(workbooks, config.hierarchySheets, (workbookName, sheet, spec) => {
    ingestHierarchySheet(builder, workbookName, sheet, spec, warnings);
  });
  ingestConfiguredSheets(workbooks, config.mappingSheets, (workbookName, sheet, spec) => {
    ingestMappingSheet(builder, workbookName, sheet, spec, warnings);
  });

  return { graph, warnings, summary: graph.summary() };
}

export function normalizeWorkbooks(parsedWorkbooks) {
  return parsedWorkbooks.map((workbook) => ({
    name: workbook.name,
    sheets: workbook.sheets.map((sheet) => ({
      name: sheet.name,
      state: sheet.state,
      hidden: Boolean(sheet.hidden),
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
