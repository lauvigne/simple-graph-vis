export type NodeKind = 'application' | 'businessCapacity' | 'entity' | 'domain' | 'regulation' | string;

export type EdgeType = 'contains' | 'mapped_to' | 'belongs_to' | string;

export interface StorageNode {
  k?: string;
  i?: string;
  t?: NodeKind;
  l?: string;
  m?: Record<string, unknown>;
  key?: string;
  id?: string;
  kind?: NodeKind;
  label?: string;
  meta?: Record<string, unknown>;
}

export interface StorageEdge {
  s?: string;
  t?: string;
  r?: EdgeType;
  source?: string;
  target?: string;
  type?: EdgeType;
  meta?: Record<string, unknown>;
}

export interface StorageSourceSheet {
  name: string;
  rowCount?: number;
  headers?: string[];
}

export interface StorageSource {
  name: string;
  sheets: StorageSourceSheet[];
}

export interface StorageData {
  version: string;
  format?: string;
  generatedAt?: string;
  sources?: StorageSource[];
  workbooks?: StorageSource[];
  warnings?: string[];
  summary?: {
    workbooks?: number;
    sheets?: number;
    graph?: GraphSummary;
  };
  graph: {
    summary?: GraphSummary;
    nodes: StorageNode[];
    edges: StorageEdge[];
  };
}

export interface GraphSummary {
  nodes: number;
  edges: number;
  kinds: Record<string, number>;
}

export interface GraphNode {
  key: string;
  id: string;
  kind: NodeKind;
  label: string;
  meta: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: EdgeType;
  meta: Record<string, unknown>;
}

export interface TypedGraph {
  nodes: Map<string, GraphNode>;
  edges: GraphEdge[];
  outgoing: Map<string, GraphEdge[]>;
  incoming: Map<string, GraphEdge[]>;
  nodesByKind: Map<string, Set<string>>;
}

export interface CoverageCandidate {
  entity: string;
  coveredEntity: string;
  coveringEntity: string;
  coveredApp: string;
  coveringApp: string;
  coveredAppKey: string;
  coveringAppKey: string;
  coverage: number;
  type: 'exact' | 'near';
  coveredCount: number;
  coveringCount: number;
  overlapCount: number;
  sharedNodes: GraphNode[];
  missingNodes: GraphNode[];
  extraNodes: GraphNode[];
  directTargetsA: GraphNode[];
  directTargetsB: GraphNode[];
}

export type CoverageScopeMode = 'withinEntity' | 'crossEntity' | 'all';

export interface CoverageOptions {
  threshold: number;
  includePartialCoverage: boolean;
  maxCandidates: number;
  maxCandidatesPerEntity: number;
  maxCandidatesPerCoveredApplication?: number;
  entity?: string;
  scopeMode?: CoverageScopeMode;
}

export interface CoverageSummary {
  candidates: number;
  exact: number;
  near: number;
  coveredApplications: number;
  coveringApplications: number;
  entities: number;
}
