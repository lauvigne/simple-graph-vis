import { Injectable } from '@angular/core';
import { GraphEdge, GraphNode, GraphSummary, StorageData, StorageEdge, StorageNode, TypedGraph } from '../models/storage-data';

@Injectable({ providedIn: 'root' })
export class GraphService {
  buildGraph(storage: StorageData | null | undefined): TypedGraph {
    const graph = this.emptyGraph();
    for (const node of storage?.graph?.nodes ?? []) {
      this.ensureNode(graph, this.normalizeNode(node));
    }
    for (const edge of storage?.graph?.edges ?? []) {
      this.addEdge(graph, this.normalizeEdge(edge));
    }
    return graph;
  }

  emptyGraph(): TypedGraph {
    return {
      nodes: new Map<string, GraphNode>(),
      edges: [],
      outgoing: new Map<string, GraphEdge[]>(),
      incoming: new Map<string, GraphEdge[]>(),
      nodesByKind: new Map<string, Set<string>>(),
    };
  }

  summary(graph: TypedGraph): GraphSummary {
    const kinds: Record<string, number> = {};
    for (const [kind, keys] of graph.nodesByKind.entries()) {
      kinds[kind] = keys.size;
    }
    return {
      nodes: graph.nodes.size,
      edges: graph.edges.length,
      kinds,
    };
  }

  nodesByKind(graph: TypedGraph, kind: string): GraphNode[] {
    return Array.from(graph.nodesByKind.get(kind) ?? [])
      .map((key) => graph.nodes.get(key))
      .filter((node): node is GraphNode => Boolean(node));
  }

  outgoing(graph: TypedGraph, key: string, type?: string): GraphEdge[] {
    const edges = graph.outgoing.get(key) ?? [];
    return type ? edges.filter((edge) => edge.type === type) : edges;
  }

  incoming(graph: TypedGraph, key: string, type?: string): GraphEdge[] {
    const edges = graph.incoming.get(key) ?? [];
    return type ? edges.filter((edge) => edge.type === type) : edges;
  }

  descendants(graph: TypedGraph, startKey: string, edgeType = 'contains'): Set<string> {
    const visited = new Set<string>();
    const stack = [startKey];
    while (stack.length) {
      const current = stack.pop();
      if (!current) continue;
      for (const edge of this.outgoing(graph, current, edgeType)) {
        if (visited.has(edge.target)) continue;
        visited.add(edge.target);
        stack.push(edge.target);
      }
    }
    return visited;
  }

  closure(graph: TypedGraph, keys: Iterable<string>, edgeType = 'contains'): Set<string> {
    const result = new Set<string>();
    for (const key of keys) {
      if (!graph.nodes.has(key)) continue;
      result.add(key);
      for (const descendant of this.descendants(graph, key, edgeType)) {
        result.add(descendant);
      }
    }
    return result;
  }

  getNode(graph: TypedGraph, key: string): GraphNode | null {
    return graph.nodes.get(key) ?? null;
  }

  private ensureNode(graph: TypedGraph, node: GraphNode): GraphNode {
    const existing = graph.nodes.get(node.key);
    if (existing) return existing;
    graph.nodes.set(node.key, node);
    if (!graph.nodesByKind.has(node.kind)) {
      graph.nodesByKind.set(node.kind, new Set<string>());
    }
    graph.nodesByKind.get(node.kind)?.add(node.key);
    return node;
  }

  private addEdge(graph: TypedGraph, edge: GraphEdge): void {
    if (!edge.source || !edge.target || !edge.type) return;
    graph.edges.push(edge);
    if (!graph.outgoing.has(edge.source)) graph.outgoing.set(edge.source, []);
    if (!graph.incoming.has(edge.target)) graph.incoming.set(edge.target, []);
    graph.outgoing.get(edge.source)?.push(edge);
    graph.incoming.get(edge.target)?.push(edge);
  }

  private normalizeNode(node: StorageNode): GraphNode {
    const key = node.k ?? node.key ?? `${node.t ?? node.kind}:${node.i ?? node.id ?? node.l ?? node.label}`;
    const id = node.i ?? node.id ?? key.split(':').slice(1).join(':');
    const resolvedId = id || key;
    return {
      key,
      id: resolvedId,
      kind: node.t ?? node.kind ?? 'node',
      label: node.l ?? node.label ?? id,
      meta: node.m ?? node.meta ?? {},
    };
  }

  private normalizeEdge(edge: StorageEdge): GraphEdge {
    return {
      source: edge.s ?? edge.source ?? '',
      target: edge.t ?? edge.target ?? '',
      type: edge.r ?? edge.type ?? '',
      meta: edge.meta ?? {},
    };
  }
}
