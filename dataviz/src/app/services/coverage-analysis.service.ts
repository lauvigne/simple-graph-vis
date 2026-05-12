import { Injectable, inject } from '@angular/core';
import { CoverageCandidate, CoverageOptions, CoverageSummary, GraphNode, TypedGraph } from '../models/storage-data';
import { GraphService } from './graph.service';

interface AppInfo {
  app: GraphNode;
  entity: string;
  directTargets: Set<string>;
  scope: Set<string>;
}

@Injectable({ providedIn: 'root' })
export class CoverageAnalysisService {
  private readonly graphService = inject(GraphService);

  buildCandidates(graph: TypedGraph, options: CoverageOptions): CoverageCandidate[] {
    const scopeMode = options.scopeMode ?? 'all';
    const appInfos = this.buildAppInfos(graph);
    const coveredApps = appInfos.filter((info) => !options.entity || info.entity === options.entity);

    const candidates: CoverageCandidate[] = [];
    const scopeIndex = this.buildScopeIndex(appInfos);

    for (const covered of coveredApps) {
      const appCandidates = this.buildAppCandidates(graph, covered, scopeIndex, options, scopeMode);
      candidates.push(...appCandidates);
    }

    return this.limitCandidatesByEntity(this.sortCandidates(candidates), options)
      .slice(0, options.maxCandidates);
  }

  private sortCandidates(candidates: CoverageCandidate[]): CoverageCandidate[] {
    return candidates.sort((left, right) => {
      if (left.type !== right.type) return left.type === 'exact' ? -1 : 1;
      if (right.coverage !== left.coverage) return right.coverage - left.coverage;
      if (left.coveredEntity !== right.coveredEntity) return left.coveredEntity.localeCompare(right.coveredEntity);
      if (left.coveringEntity !== right.coveringEntity) return left.coveringEntity.localeCompare(right.coveringEntity);
      if (left.coveredApp !== right.coveredApp) return left.coveredApp.localeCompare(right.coveredApp);
      return left.coveringApp.localeCompare(right.coveringApp);
    });
  }

  private limitCandidatesByEntity(candidates: CoverageCandidate[], options: CoverageOptions): CoverageCandidate[] {
    const countsByEntity = new Map<string, number>();
    return candidates.filter((candidate) => {
      const count = countsByEntity.get(candidate.coveredEntity) ?? 0;
      if (count >= options.maxCandidatesPerEntity) return false;
      countsByEntity.set(candidate.coveredEntity, count + 1);
      return true;
    });
  }

  summarize(candidates: CoverageCandidate[]): CoverageSummary {
    return {
      candidates: candidates.length,
      exact: candidates.filter((candidate) => candidate.type === 'exact').length,
      near: candidates.filter((candidate) => candidate.type === 'near').length,
      coveredApplications: new Set(candidates.map((candidate) => candidate.coveredAppKey)).size,
      coveringApplications: new Set(candidates.map((candidate) => candidate.coveringAppKey)).size,
      entities: new Set(candidates.flatMap((candidate) => [candidate.coveredEntity, candidate.coveringEntity])).size,
    };
  }

  entities(graph: TypedGraph): string[] {
    return this.graphService.nodesByKind(graph, 'entity').map((node) => node.label).sort((a, b) => a.localeCompare(b));
  }

  private buildAppInfos(graph: TypedGraph): AppInfo[] {
    return this.graphService.nodesByKind(graph, 'application').map((app) => {
      const entities = this.graphService.outgoing(graph, app.key, 'belongs_to')
        .map((edge) => this.graphService.getNode(graph, edge.target))
        .filter((node): node is GraphNode => Boolean(node));
      const directTargets = new Set(this.graphService.outgoing(graph, app.key, 'mapped_to').map((edge) => edge.target));
      const scope = this.graphService.closure(graph, directTargets, 'contains');
      return {
        app,
        entity: entities[0]?.label ?? '__unassigned__',
        directTargets,
        scope,
      };
    }).filter((info) => info.scope.size > 0);
  }

  private buildScopeIndex(apps: AppInfo[]): Map<string, AppInfo[]> {
    const scopeIndex = new Map<string, AppInfo[]>();
    for (const info of apps) {
      for (const nodeKey of info.scope) {
        if (!scopeIndex.has(nodeKey)) scopeIndex.set(nodeKey, []);
        scopeIndex.get(nodeKey)?.push(info);
      }
    }
    return scopeIndex;
  }

  private buildAppCandidates(
    graph: TypedGraph,
    covered: AppInfo,
    scopeIndex: Map<string, AppInfo[]>,
    options: CoverageOptions,
    scopeMode: 'withinEntity' | 'crossEntity' | 'all',
  ): CoverageCandidate[] {
    const candidates: CoverageCandidate[] = [];
    const overlapCounts = new Map<AppInfo, number>();
    for (const nodeKey of covered.scope) {
      for (const covering of scopeIndex.get(nodeKey) ?? []) {
        if (covering.app.key === covered.app.key) continue;
        if (scopeMode === 'withinEntity' && covering.entity !== covered.entity) continue;
        if (scopeMode === 'crossEntity' && covering.entity === covered.entity) continue;
        overlapCounts.set(covering, (overlapCounts.get(covering) ?? 0) + 1);
      }
    }

    for (const [covering, overlapCount] of overlapCounts.entries()) {
      const coverage = overlapCount / covered.scope.size;
      const exact = coverage === 1;
      const near = coverage >= options.threshold && coverage < 1;
      if (!exact && !(options.includePartialCoverage && near)) continue;

      const shared = this.intersection(covered.scope, covering.scope);
      const missing = this.difference(covered.scope, covering.scope);
      const extra = this.difference(covering.scope, covered.scope);
      candidates.push({
        entity: covered.entity,
        coveredEntity: covered.entity,
        coveringEntity: covering.entity,
        coveredApp: covered.app.label,
        coveringApp: covering.app.label,
        coveredAppKey: covered.app.key,
        coveringAppKey: covering.app.key,
        coverage,
        type: exact ? 'exact' : 'near',
        coveredCount: covered.scope.size,
        coveringCount: covering.scope.size,
        overlapCount,
        sharedNodes: this.nodesFromKeys(graph, shared),
        missingNodes: this.nodesFromKeys(graph, missing),
        extraNodes: this.nodesFromKeys(graph, extra),
        directTargetsA: this.nodesFromKeys(graph, covered.directTargets),
        directTargetsB: this.nodesFromKeys(graph, covering.directTargets),
      });
    }
    return this.sortCandidates(candidates).slice(0, options.maxCandidatesPerCoveredApplication ?? 20);
  }

  private nodesFromKeys(graph: TypedGraph, keys: Iterable<string>): GraphNode[] {
    return Array.from(keys)
      .map((key) => this.graphService.getNode(graph, key))
      .filter((node): node is GraphNode => Boolean(node))
      .sort((left, right) => {
        if (left.kind !== right.kind) return left.kind.localeCompare(right.kind);
        return left.label.localeCompare(right.label);
      });
  }

  private intersection(left: Set<string>, right: Set<string>): Set<string> {
    return new Set(Array.from(left).filter((value) => right.has(value)));
  }

  private difference(left: Set<string>, right: Set<string>): Set<string> {
    return new Set(Array.from(left).filter((value) => !right.has(value)));
  }
}
