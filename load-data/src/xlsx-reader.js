function requireSheetJs() {
  const xlsx = globalThis.XLSX;
  if (!xlsx) {
    throw new Error([
      "SheetJS is not loaded.",
      "Check that the CDN script is reachable:",
      "https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js",
    ].join(" "));
  }
  return xlsx;
}

function attachRowNumber(record, rowNumber) {
  Object.defineProperty(record, "__rowNumber", {
    value: rowNumber,
    enumerable: false,
  });
  return record;
}

function normalizeCellValue(value) {
  if (value === null || value === undefined) return "";
  if (value instanceof Date) return value.toISOString();
  return value;
}

function trimTrailingEmptyCells(row) {
  const values = row.map(normalizeCellValue);
  while (values.length && String(values[values.length - 1] ?? "").trim() === "") {
    values.pop();
  }
  return values;
}

function rowsToRecords(rawRows) {
  if (!rawRows.length) {
    return { headers: [], rows: [] };
  }

  const headers = rawRows[0].map((value) => String(value ?? "").trim());
  const rows = rawRows
    .slice(1)
    .map((row, index) => ({ row, rowNumber: index + 2 }))
    .filter(({ row }) => row.some((value) => String(value ?? "").trim() !== ""))
    .map(({ row, rowNumber }) => {
      const record = {};
      headers.forEach((header, index) => {
        if (!header) return;
        record[header] = row[index] ?? "";
      });
      return attachRowNumber(record, rowNumber);
    });

  return { headers, rows };
}

function sheetState(sheetMetadata) {
  const hidden = Number(sheetMetadata?.Hidden ?? 0);
  if (hidden === 1) return "hidden";
  if (hidden === 2) return "veryHidden";
  return "visible";
}

function visibleSheetNames(workbook) {
  const sheetMetadata = workbook.Workbook?.Sheets ?? [];
  const stateByName = new Map(sheetMetadata.map((sheet) => [sheet.name, sheetState(sheet)]));
  return workbook.SheetNames
    .map((name) => ({ name, state: stateByName.get(name) ?? "visible" }))
    .filter((sheet) => sheet.state === "visible");
}

function worksheetToSheet(workbook, sheetInfo) {
  const xlsx = requireSheetJs();
  const worksheet = workbook.Sheets[sheetInfo.name];
  if (!worksheet) {
    return {
      name: sheetInfo.name,
      state: sheetInfo.state,
      hidden: sheetInfo.state !== "visible",
      headers: [],
      rows: [],
      rawRows: [],
    };
  }

  const rawRows = xlsx.utils.sheet_to_json(worksheet, {
    header: 1,
    blankrows: true,
    defval: "",
    raw: false,
  }).map(trimTrailingEmptyCells);
  const parsed = rowsToRecords(rawRows);
  return {
    name: sheetInfo.name,
    state: sheetInfo.state,
    hidden: sheetInfo.state !== "visible",
    headers: parsed.headers,
    rows: parsed.rows,
    rawRows,
  };
}

export async function readXlsxFile(file) {
  const xlsx = requireSheetJs();
  const arrayBuffer = await file.arrayBuffer();
  const workbook = xlsx.read(arrayBuffer, {
    type: "array",
    cellDates: true,
    dense: false,
  });

  return {
    name: file.name,
    sheets: visibleSheetNames(workbook).map((sheetInfo) => worksheetToSheet(workbook, sheetInfo)),
  };
}
