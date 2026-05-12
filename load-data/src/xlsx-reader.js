function view(bytes) {
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
}

function readU16(v, offset) {
  return v.getUint16(offset, true);
}

function readU32(v, offset) {
  return v.getUint32(offset, true);
}

function bytesToString(bytes) {
  return new TextDecoder("utf-8").decode(bytes);
}

function findEndOfCentralDirectory(bytes) {
  const signature = 0x06054b50;
  const minOffset = Math.max(0, bytes.length - 0x10000 - 22);
  for (let offset = bytes.length - 22; offset >= minOffset; offset--) {
    if (readU32(view(bytes), offset) === signature) return offset;
  }
  throw new Error("ZIP end-of-central-directory record not found");
}

async function inflateRaw(bytes) {
  if (typeof DecompressionStream === "undefined") {
    throw new Error("This browser does not support DecompressionStream");
  }
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

async function unzipXlsx(arrayBuffer) {
  const bytes = new Uint8Array(arrayBuffer);
  const dv = view(bytes);
  const eocd = findEndOfCentralDirectory(bytes);
  const entryCount = readU16(dv, eocd + 10);
  const centralDirOffset = readU32(dv, eocd + 16);
  const files = new Map();
  let offset = centralDirOffset;

  for (let index = 0; index < entryCount; index++) {
    const signature = readU32(dv, offset);
    if (signature !== 0x02014b50) {
      break;
    }

    const compressionMethod = readU16(dv, offset + 10);
    const compressedSize = readU32(dv, offset + 20);
    const uncompressedSize = readU32(dv, offset + 24);
    const fileNameLength = readU16(dv, offset + 28);
    const extraLength = readU16(dv, offset + 30);
    const commentLength = readU16(dv, offset + 32);
    const relativeOffset = readU32(dv, offset + 42);
    const fileNameBytes = bytes.slice(offset + 46, offset + 46 + fileNameLength);
    const fileName = bytesToString(fileNameBytes);

    const localSignature = readU32(dv, relativeOffset);
    if (localSignature !== 0x04034b50) {
      throw new Error(`Invalid local file header for ${fileName}`);
    }
    const localNameLength = readU16(dv, relativeOffset + 26);
    const localExtraLength = readU16(dv, relativeOffset + 28);
    const dataStart = relativeOffset + 30 + localNameLength + localExtraLength;
    const dataEnd = dataStart + compressedSize;
    const compressedBytes = bytes.slice(dataStart, dataEnd);

    let contentBytes;
    if (compressionMethod === 0) {
      contentBytes = compressedBytes;
    } else if (compressionMethod === 8) {
      contentBytes = await inflateRaw(compressedBytes);
    } else {
      throw new Error(`Unsupported ZIP compression method ${compressionMethod} for ${fileName}`);
    }

    if (contentBytes.length !== uncompressedSize && uncompressedSize !== 0) {
      // Do not fail hard on size mismatch; some producers omit exact sizes.
    }
    files.set(fileName, contentBytes);
    offset += 46 + fileNameLength + extraLength + commentLength;
  }

  return files;
}

function textFromFile(files, path) {
  const bytes = files.get(path);
  if (!bytes) return null;
  return bytesToString(bytes);
}

function parseXml(text) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(text, "application/xml");
  const error = doc.querySelector("parsererror");
  if (error) {
    throw new Error(`Invalid XML content: ${error.textContent?.trim() ?? "unknown error"}`);
  }
  return doc;
}

function getTextValue(node) {
  return node?.textContent?.replace(/\r/g, "").trim() ?? "";
}

function parseSharedStrings(files) {
  const xml = textFromFile(files, "xl/sharedStrings.xml");
  if (!xml) return [];
  const doc = parseXml(xml);
  return Array.from(doc.getElementsByTagName("si")).map((node) => getTextValue(node));
}

function resolveSheetPath(target) {
  const normalized = target.replace(/^\//, "");
  return normalized.startsWith("xl/") ? normalized : `xl/${normalized}`;
}

function parseWorkbook(files) {
  const workbookXml = textFromFile(files, "xl/workbook.xml");
  const relsXml = textFromFile(files, "xl/_rels/workbook.xml.rels");
  if (!workbookXml || !relsXml) {
    throw new Error("Workbook structure is incomplete: missing xl/workbook.xml or xl/_rels/workbook.xml.rels");
  }

  const workbookDoc = parseXml(workbookXml);
  const relsDoc = parseXml(relsXml);
  const rels = new Map();
  Array.from(relsDoc.getElementsByTagName("Relationship")).forEach((rel) => {
    rels.set(rel.getAttribute("Id"), resolveSheetPath(rel.getAttribute("Target") ?? ""));
  });

  return Array.from(workbookDoc.getElementsByTagName("sheet")).map((sheet) => ({
    name: sheet.getAttribute("name") ?? "",
    path: rels.get(sheet.getAttribute("r:id")) ?? null,
  })).filter((sheet) => Boolean(sheet.path));
}

function cellRefToColumnIndex(ref) {
  const letters = ref.replace(/\d+/g, "");
  let index = 0;
  for (let i = 0; i < letters.length; i++) {
    index = index * 26 + (letters.charCodeAt(i) - 64);
  }
  return index - 1;
}

function attachRowNumber(record, rowNumber) {
  Object.defineProperty(record, "__rowNumber", {
    value: rowNumber,
    enumerable: false,
  });
  return record;
}

function cellValue(cell, sharedStrings) {
  const type = cell.getAttribute("t");
  const formulaValue = cell.getElementsByTagName("v")[0];
  const inlineString = cell.getElementsByTagName("is")[0];
  if (type === "s") {
    const index = Number(getTextValue(formulaValue));
    return sharedStrings[index] ?? "";
  }
  if (type === "inlineStr") {
    return getTextValue(inlineString);
  }
  if (type === "b") {
    return getTextValue(formulaValue) === "1";
  }
  if (type === "str") {
    return getTextValue(formulaValue);
  }
  const text = getTextValue(formulaValue);
  if (text === "") return "";
  const number = Number(text);
  return Number.isNaN(number) ? text : number;
}

function sheetXmlToRows(xmlText, sharedStrings) {
  const doc = parseXml(xmlText);
  const rawRows = [];
  const rowNodes = Array.from(doc.getElementsByTagName("row"));
  for (const rowNode of rowNodes) {
    const cells = Array.from(rowNode.getElementsByTagName("c"));
    const indexed = [];
    for (const cell of cells) {
      const ref = cell.getAttribute("r") ?? "";
      const colIndex = cellRefToColumnIndex(ref);
      indexed[colIndex] = cellValue(cell, sharedStrings);
    }
    rawRows.push(indexed);
  }
  if (!rawRows.length) return { headers: [], rows: [], rawRows: [] };
  const rows = rawRows.slice();
  const headers = rows.shift().map((value) => String(value ?? "").trim());
  const data = rows
    .map((row, index) => ({ row, rowNumber: index + 2 }))
    .filter(({ row }) => row.some((value) => String(value ?? "").trim() !== ""))
    .map(({ row, rowNumber }) => {
      const record = {};
      headers.forEach((header, index) => {
        record[header] = row[index] ?? "";
      });
      return attachRowNumber(record, rowNumber);
    });
  return { headers, rows: data, rawRows };
}

export async function readXlsxFile(file) {
  const files = await unzipXlsx(await file.arrayBuffer());
  const sharedStrings = parseSharedStrings(files);
  const sheets = parseWorkbook(files).map((sheet) => {
    const xml = textFromFile(files, sheet.path);
    if (!xml) {
      return { name: sheet.name, headers: [], rows: [] };
    }
    const parsed = sheetXmlToRows(xml, sharedStrings);
    return { name: sheet.name, ...parsed };
  });

  return {
    name: file.name,
    sheets,
  };
}
