import { normalizeText, slugify, stableKey } from "./utils.js";

export class TypedGraph {
  constructor() {
    this.nodes = new Map();
    this.edges = [];
    this.outgoing = new Map();
    this.incoming = new Map();
    this.nodesByKind = new Map();
  }

  nodeKey(kind, id) {
    return `${kind}:${id}`;
  }

  ensureNode({ kind, id, label, meta = {} }) {
    const key = this.nodeKey(kind, id);
    const existing = this.nodes.get(key);
    if (existing) {
      existing.label ||= label ?? id;
      existing.meta = { ...existing.meta, ...meta };
      return existing;
    }

    const node = {
      key,
      id,
      kind,
      label: label ?? id,
      meta: { ...meta },
    };
    this.nodes.set(key, node);
    if (!this.nodesByKind.has(kind)) {
      this.nodesByKind.set(kind, new Set());
    }
    this.nodesByKind.get(kind).add(key);
    return node;
  }

  addEdge(sourceKey, targetKey, type, meta = {}) {
    const edge = {
      key: `${sourceKey} -> ${targetKey} [${type}]`,
      source: sourceKey,
      target: targetKey,
      type,
      meta: { ...meta },
    };
    this.edges.push(edge);

    if (!this.outgoing.has(sourceKey)) this.outgoing.set(sourceKey, []);
    if (!this.incoming.has(targetKey)) this.incoming.set(targetKey, []);
    this.outgoing.get(sourceKey).push(edge);
    this.incoming.get(targetKey).push(edge);
    return edge;
  }

  getNode(key) {
    return this.nodes.get(key) ?? null;
  }

  getNodesByKind(kind) {
    return Array.from(this.nodesByKind.get(kind) ?? []).map((key) => this.getNode(key)).filter(Boolean);
  }

  getOutgoing(key, type = null) {
    const edges = this.outgoing.get(key) ?? [];
    return type ? edges.filter((edge) => edge.type === type) : edges.slice();
  }

  getIncoming(key, type = null) {
    const edges = this.incoming.get(key) ?? [];
    return type ? edges.filter((edge) => edge.type === type) : edges.slice();
  }

  descendants(startKey, edgeType = "contains") {
    const visited = new Set();
    const stack = [startKey];
    while (stack.length) {
      const key = stack.pop();
      const outgoing = this.getOutgoing(key, edgeType);
      for (const edge of outgoing) {
        if (visited.has(edge.target)) continue;
        visited.add(edge.target);
        stack.push(edge.target);
      }
    }
    return visited;
  }

  ancestors(startKey, edgeType = "contains") {
    const visited = new Set();
    const stack = [startKey];
    while (stack.length) {
      const key = stack.pop();
      const incoming = this.getIncoming(key, edgeType);
      for (const edge of incoming) {
        if (visited.has(edge.source)) continue;
        visited.add(edge.source);
        stack.push(edge.source);
      }
    }
    return visited;
  }

  closure(keys, edgeType = "contains") {
    const result = new Set();
    for (const key of keys) {
      if (!this.nodes.has(key)) continue;
      result.add(key);
      for (const desc of this.descendants(key, edgeType)) {
        result.add(desc);
      }
    }
    return result;
  }

  subgraph(nodeKeys) {
    const keySet = new Set(nodeKeys);
    return {
      nodes: Array.from(this.nodes.values()).filter((node) => keySet.has(node.key)),
      edges: this.edges.filter((edge) => keySet.has(edge.source) && keySet.has(edge.target)),
    };
  }

  summary() {
    return {
      nodes: this.nodes.size,
      edges: this.edges.length,
      kinds: Array.from(this.nodesByKind.entries()).reduce((acc, [kind, keys]) => {
        acc[kind] = keys.size;
        return acc;
      }, {}),
    };
  }
}

export function makeNodeId(kind, parts) {
  return stableKey([kind, ...parts]);
}

export function createPathNodeId(kind, parts) {
  return `${kind}:${parts.map((part) => slugify(part)).filter(Boolean).join("/")}`;
}

export function isHierarchyEdge(edge) {
  return edge.type === "contains";
}

export function groupBy(values, keyFn) {
  const map = new Map();
  for (const value of values) {
    const key = keyFn(value);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(value);
  }
  return map;
}

export function unique(values) {
  return Array.from(new Set(values));
}

export function sortByLabel(items) {
  return items.slice().sort((a, b) => a.label.localeCompare(b.label, "fr"));
}

export function normalizeGraphId(value) {
  return normalizeText(value).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

