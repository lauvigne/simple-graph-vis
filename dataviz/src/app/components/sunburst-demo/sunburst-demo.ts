import { Component, computed, inject } from '@angular/core';
import { GraphNode, TypedGraph } from '../../models/storage-data';
import { SunburstData, SunburstNode } from '../../models/sunburst-data';
import { GraphService } from '../../services/graph.service';
import { GraphState } from '../../services/graph-state';
import { BusinessCapabilitySunburst } from '../business-capability-sunburst/business-capability-sunburst';

@Component({
  selector: 'app-sunburst-demo',
  imports: [BusinessCapabilitySunburst],
  templateUrl: './sunburst-demo.html',
  styleUrl: './sunburst-demo.scss',
})
export class SunburstDemo {
  private readonly graphService = inject(GraphService);
  private readonly graphState = inject(GraphState);

  readonly capabilityCountData = computed<SunburstData>(() => ({
    label: 'Business capabilities - niveaux 1 et 2',
    metric: {
      key: 'capabilityCount',
      label: 'Capacités',
    },
    children: this.buildLevelTwoNodes((graph, levelTwo) => this.businessCapabilitySubtreeSize(graph, levelTwo)),
  }));

  readonly tcoData = computed<SunburstData>(() => ({
    label: 'Business capabilities - TCO simulé',
    metric: {
      key: 'simulatedTco',
      label: 'TCO simulé',
      unit: 'kEUR',
    },
    children: this.buildLevelTwoNodes((graph, levelTwo) => this.simulatedTcoForCapability(graph, levelTwo)),
  }));

  private buildLevelTwoNodes(valueForLevelTwo: (graph: TypedGraph, levelTwo: GraphNode) => number): SunburstNode[] {
    const graph = this.graphState.graph();
    const roots = this.businessCapabilityRoots(graph);
    return roots.map((root) => ({
      id: root.key,
      label: this.capabilityLabel(root),
      children: this.childCapabilities(graph, root)
        .map((child) => ({
          id: child.key,
          label: this.capabilityLabel(child),
          value: valueForLevelTwo(graph, child),
          meta: {
            key: child.key,
            code: child.meta['code'],
          },
        }))
        .filter((node) => (node.value ?? 0) > 0),
      meta: {
        key: root.key,
        code: root.meta['code'],
      },
    })).filter((node) => (node.children?.length ?? 0) > 0);
  }

  private businessCapabilityRoots(graph: TypedGraph): GraphNode[] {
    return this.graphService.nodesByKind(graph, 'businessCapacity')
      .filter((node) => this.graphService.incoming(graph, node.key, 'contains').length === 0)
      .sort(this.sortByCodeThenLabel);
  }

  private childCapabilities(graph: TypedGraph, node: GraphNode): GraphNode[] {
    return this.graphService.outgoing(graph, node.key, 'contains')
      .map((edge) => this.graphService.getNode(graph, edge.target))
      .filter((child): child is GraphNode => child?.kind === 'businessCapacity')
      .sort(this.sortByCodeThenLabel);
  }

  private businessCapabilitySubtreeSize(graph: TypedGraph, node: GraphNode): number {
    return this.businessCapabilityScope(graph, node).size;
  }

  private simulatedTcoForCapability(graph: TypedGraph, node: GraphNode): number {
    const appCount = this.applicationsIntersectingCapability(graph, node).size;
    return appCount * 100;
  }

  private applicationsIntersectingCapability(graph: TypedGraph, node: GraphNode): Set<string> {
    const capabilityScope = this.businessCapabilityScope(graph, node);
    const applications = new Set<string>();
    for (const app of this.graphService.nodesByKind(graph, 'application')) {
      const mappedTargets = this.graphService.outgoing(graph, app.key, 'mapped_to').map((edge) => edge.target);
      const appScope = this.graphService.closure(graph, mappedTargets, 'contains');
      if (Array.from(appScope).some((key) => capabilityScope.has(key))) {
        applications.add(app.key);
      }
    }
    return applications;
  }

  private businessCapabilityScope(graph: TypedGraph, node: GraphNode): Set<string> {
    return this.graphService.closure(graph, [node.key], 'contains');
  }

  private capabilityLabel(node: GraphNode): string {
    const code = node.meta['code'];
    return typeof code === 'string' && code.trim() ? `${code.trim()}#${node.label}` : node.label;
  }

  private sortByCodeThenLabel(left: GraphNode, right: GraphNode): number {
    const leftCode = typeof left.meta['code'] === 'string' ? left.meta['code'] : '';
    const rightCode = typeof right.meta['code'] === 'string' ? right.meta['code'] : '';
    if (leftCode && rightCode) return leftCode.localeCompare(rightCode, undefined, { numeric: true });
    if (leftCode !== rightCode) return leftCode ? -1 : 1;
    return left.label.localeCompare(right.label);
  }
}
