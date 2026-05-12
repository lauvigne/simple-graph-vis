import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { GraphNode, TypedGraph } from '../../models/storage-data';
import { GraphService } from '../../services/graph.service';
import { GraphState } from '../../services/graph-state';

interface BusinessCapabilityRow {
  key: string;
  code: string;
  levels: string[];
  depth: number;
  label: string;
}

@Component({
  selector: 'app-business-capability-table',
  imports: [CommonModule],
  templateUrl: './business-capability-table.html',
  styleUrl: './business-capability-table.scss',
})
export class BusinessCapabilityTable {
  private readonly graphService = inject(GraphService);
  private readonly graphState = inject(GraphState);

  readonly query = signal('');
  readonly rows = computed(() => this.buildRows(this.graphState.graph()));
  readonly filteredRows = computed(() => {
    const normalizedQuery = this.query().trim().toLowerCase();
    if (!normalizedQuery) return this.rows();
    return this.rows().filter((row) =>
      [row.code, row.label, row.key, ...row.levels].some((value) => value.toLowerCase().includes(normalizedQuery)),
    );
  });
  readonly duplicateLabels = computed(() => this.countDuplicates(this.rows().map((row) => row.label)));
  readonly duplicatePaths = computed(() => this.countDuplicates(this.rows().map((row) => row.levels.join(' / '))));
  readonly maxDepth = computed(() => Math.max(0, ...this.rows().map((row) => row.depth)));

  setQuery(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
  }

  private buildRows(graph: TypedGraph): BusinessCapabilityRow[] {
    return this.graphService.nodesByKind(graph, 'businessCapacity')
      .map((node) => this.toRow(graph, node))
      .sort((left, right) => {
        if (left.code && right.code) return left.code.localeCompare(right.code, undefined, { numeric: true });
        if (left.code !== right.code) return left.code ? -1 : 1;
        return left.levels.join(' / ').localeCompare(right.levels.join(' / '));
      });
  }

  private toRow(graph: TypedGraph, node: GraphNode): BusinessCapabilityRow {
    const path = this.pathToRoot(graph, node);
    const levels = Array.from({ length: 5 }, (_, index) => path[index]?.label ?? '');
    return {
      key: node.key,
      code: this.code(node),
      levels,
      depth: path.length,
      label: node.label,
    };
  }

  private pathToRoot(graph: TypedGraph, node: GraphNode): GraphNode[] {
    const path: GraphNode[] = [];
    const visited = new Set<string>();
    let current: GraphNode | null = node;
    while (current && !visited.has(current.key)) {
      path.unshift(current);
      visited.add(current.key);
      current = this.parentCapability(graph, current);
    }
    return path;
  }

  private parentCapability(graph: TypedGraph, node: GraphNode): GraphNode | null {
    const parents = this.graphService.incoming(graph, node.key, 'contains')
      .map((edge) => this.graphService.getNode(graph, edge.source))
      .filter((parent): parent is GraphNode => parent?.kind === 'businessCapacity')
      .sort((left, right) => this.code(left).localeCompare(this.code(right), undefined, { numeric: true }));
    return parents[0] ?? null;
  }

  private code(node: GraphNode): string {
    const code = node.meta['code'];
    return typeof code === 'string' ? code.trim() : '';
  }

  private countDuplicates(values: string[]): number {
    const counts = new Map<string, number>();
    for (const value of values) {
      if (!value) continue;
      counts.set(value, (counts.get(value) ?? 0) + 1);
    }
    return Array.from(counts.values()).filter((count) => count > 1).length;
  }
}
