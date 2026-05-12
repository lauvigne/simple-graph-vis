export function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

export function slugify(value) {
  return normalizeText(value)
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function escapeXml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function csvEscape(value) {
  const text = String(value ?? "");
  return /[;"\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function matchHeader(headers, candidates) {
  const list = (Array.isArray(candidates) ? candidates.flat() : [candidates])
    .map((candidate) => String(candidate ?? "").trim())
    .filter(Boolean);
  if (!list.length) return null;
  const normalized = headers.map((header) => [header, normalizeText(header)]);
  for (const candidate of list) {
    const candidateNorm = normalizeText(candidate);
    const exact = normalized.find(([, norm]) => norm === candidateNorm);
    if (exact) return exact[0];
  }
  for (const candidate of list) {
    const candidateNorm = normalizeText(candidate);
    const partial = normalized.find(([, norm]) => norm.includes(candidateNorm));
    if (partial) return partial[0];
  }
  return null;
}

export function findSheetByName(workbook, sheetNameSpec) {
  const specs = Array.isArray(sheetNameSpec) ? sheetNameSpec : [sheetNameSpec];
  const normalizedSpecs = specs.map((spec) => {
    if (spec instanceof RegExp) return spec;
    return normalizeText(spec);
  });

  return workbook.sheets.find((sheet) => {
    const normalizedSheetName = normalizeText(sheet.name);
    return normalizedSpecs.some((spec) => {
      if (spec instanceof RegExp) return spec.test(sheet.name);
      return normalizedSheetName.includes(spec);
    });
  }) ?? null;
}

export function stableKey(parts) {
  return parts
    .map((part) => normalizeText(part))
    .filter(Boolean)
    .join("::");
}
