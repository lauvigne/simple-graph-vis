import { defaultConfig, demoWorkbookRows } from "./config.js";
import { TypedGraph } from "./graph.js";
import { escapeHtml } from "./utils.js";
import { createStorageData } from "./storage.js";
import { readXlsxFile } from "./xlsx-reader.js";
import { buildGraphFromWorkbooks, normalizeWorkbooks } from "./data-loader.js";

const els = {
  fileInput: document.getElementById("fileInput"),
  loadFiles: document.getElementById("loadFiles"),
  loadDemo: document.getElementById("loadDemo"),
  reset: document.getElementById("reset"),
  config: document.getElementById("config"),
  loadConfig: document.getElementById("loadConfig"),
  status: document.getElementById("status"),
  warnings: document.getElementById("warnings"),
  summary: document.getElementById("summary"),
  graphSummary: document.getElementById("graphSummary"),
  workbookList: document.getElementById("workbookList"),
  downloadGraph: document.getElementById("downloadGraph"),
  downloadStorage: document.getElementById("downloadStorage"),
};

const state = {
  config: structuredClone(defaultConfig),
  files: [],
  workbooks: [],
  graph: new TypedGraph(),
  warnings: [],
};

els.config.value = JSON.stringify(state.config, null, 2);

function setStatus(message, tone = "info") {
  els.status.innerHTML = `<span class="badge ${tone}">${escapeHtml(message)}</span>`;
}

function loadConfigFromTextarea() {
  const parsed = JSON.parse(els.config.value);
  state.config = parsed;
  return parsed;
}

function workbookRowCount(workbook) {
  return workbook.sheets.reduce((sum, sheet) => sum + sheet.rows.length, 0);
}

function renderWorkbooks(workbooks) {
  if (!workbooks.length) {
    els.workbookList.innerHTML = `<div class="empty">Aucun fichier chargé.</div>`;
    return;
  }
  els.workbookList.innerHTML = workbooks.map((workbook) => `
    <div class="summary-card">
      <strong>${escapeHtml(workbook.name)}</strong>
      <span>${workbook.sheets.length} onglet(s) · ${workbookRowCount(workbook)} ligne(s)</span>
      <div class="small">${workbook.sheets.map((sheet) => escapeHtml(sheet.name)).join(" · ")}</div>
    </div>
  `).join("");
}

function renderWarnings(warnings) {
  if (!warnings.length) {
    els.warnings.innerHTML = `<div class="empty">Aucun avertissement.</div>`;
    return;
  }
  els.warnings.innerHTML = warnings.map((warning) => `<div class="warning-item">${escapeHtml(warning)}</div>`).join("");
}

function renderGraphSummary(graphSummary) {
  const kinds = Object.entries(graphSummary.kinds)
    .map(([kind, count]) => `<span class="badge neutral">${escapeHtml(kind)}: ${count}</span>`)
    .join(" ");
  els.graphSummary.innerHTML = `
    <div class="metric-grid">
      <div class="metric"><div class="label">Nœuds</div><div class="value">${graphSummary.nodes}</div></div>
      <div class="metric"><div class="label">Arêtes</div><div class="value">${graphSummary.edges}</div></div>
      <div class="metric"><div class="label">Types</div><div class="value">${Object.keys(graphSummary.kinds).length}</div></div>
    </div>
    <div class="small">${kinds}</div>
  `;
}

function renderSummary(workbooks, graphSummary) {
  const rowCount = workbooks.reduce((sum, workbook) => sum + workbookRowCount(workbook), 0);
  const sheetCount = workbooks.reduce((sum, workbook) => sum + workbook.sheets.length, 0);
  els.summary.innerHTML = `
    <div class="metric-grid">
      <div class="metric"><div class="label">Classeurs</div><div class="value">${workbooks.length}</div><div class="delta">chargés</div></div>
      <div class="metric"><div class="label">Onglets</div><div class="value">${sheetCount}</div><div class="delta">lus</div></div>
      <div class="metric"><div class="label">Lignes Excel</div><div class="value">${rowCount}</div><div class="delta">normalisées</div></div>
      <div class="metric"><div class="label">Applications</div><div class="value">${graphSummary.kinds?.application ?? 0}</div><div class="delta">dans le graphe</div></div>
    </div>
  `;
}

async function rebuildFromWorkbooks(workbooks) {
  try {
    const config = loadConfigFromTextarea();
    state.workbooks = normalizeWorkbooks(workbooks);
    const { graph, warnings, summary } = buildGraphFromWorkbooks(state.workbooks, config);
    state.graph = graph;
    state.warnings = warnings;
    renderWorkbooks(state.workbooks);
    renderWarnings(warnings);
    renderGraphSummary(summary);
    renderSummary(state.workbooks, summary);
    setStatus(`Import réussi: ${state.workbooks.length} fichier(s)`, "good");
  } catch (error) {
    console.error(error);
    setStatus("Erreur d'import", "warn");
    els.warnings.innerHTML = `<div class="warning-item">${escapeHtml(error.message || String(error))}</div>`;
  }
}

async function loadFiles(files) {
  if (!files.length) return;
  setStatus("Lecture des classeurs…", "info");
  const parsed = [];
  for (const file of files) {
    const workbook = await readXlsxFile(file);
    parsed.push(workbook);
  }
  await rebuildFromWorkbooks(parsed);
}

function resetAll() {
  state.files = [];
  state.workbooks = [];
  state.graph = new TypedGraph();
  state.warnings = [];
  els.fileInput.value = "";
  els.workbookList.innerHTML = `<div class="empty">Aucun fichier chargé.</div>`;
  els.warnings.innerHTML = `<div class="empty">Aucun avertissement.</div>`;
  els.summary.innerHTML = `<div class="empty">Chargez un classeur pour construire le graphe.</div>`;
  els.graphSummary.innerHTML = `<div class="empty">Les statistiques du graphe apparaîtront ici.</div>`;
  setStatus("Prêt", "neutral");
}

function demoWorkbooks() {
  return [{
    name: "demo.xlsx",
    sheets: demoWorkbookRows.sheets.map((sheet) => ({
      name: sheet.name,
      headers: sheet.headers,
      rows: sheet.rows,
    })),
  }];
}

function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

els.fileInput.addEventListener("change", async () => {
  const files = Array.from(els.fileInput.files ?? []);
  if (!files.length) return;
  await loadFiles(files);
});

els.loadFiles.addEventListener("click", async () => {
  const files = Array.from(els.fileInput.files ?? []);
  await loadFiles(files);
});

els.loadDemo.addEventListener("click", async () => {
  await rebuildFromWorkbooks(demoWorkbooks());
});

els.loadConfig.addEventListener("click", async () => {
  try {
    loadConfigFromTextarea();
    setStatus("Configuration chargée", "good");
    if (state.workbooks.length) {
      await rebuildFromWorkbooks(state.workbooks);
    }
  } catch (error) {
    setStatus("Configuration invalide", "warn");
    els.warnings.innerHTML = `<div class="warning-item">${escapeHtml(error.message || String(error))}</div>`;
  }
});

els.reset.addEventListener("click", resetAll);
els.downloadGraph.addEventListener("click", () => {
  downloadJson("coverage_graph.json", {
    summary: state.graph.summary(),
    nodes: Array.from(state.graph.nodes.values()),
    edges: state.graph.edges,
  });
});

els.downloadStorage.addEventListener("click", () => {
  const storageData = createStorageData({
    config: state.config,
    workbooks: state.workbooks,
    graph: state.graph,
    warnings: state.warnings,
  });
  downloadJson("storage-data.json", storageData);
  setStatus("storage-data.json prêt à être sauvegardé", "good");
});

window.addEventListener("DOMContentLoaded", () => {
  resetAll();
});
