export interface TreemapNode {
  id: string;
  label: string;
  value?: number;
  children?: TreemapNode[];
  meta?: Record<string, unknown>;
}

export interface TreemapData {
  label: string;
  metric: {
    key: string;
    label: string;
    unit?: string;
  };
  children: TreemapNode[];
}

export interface TreemapTile {
  id: string;
  label: string;
  value: number;
  depth: number;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  path: string[];
  meta: Record<string, unknown>;
}
