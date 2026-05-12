import { HierarchyRectangularNode, hierarchy, treemap, treemapSquarify } from 'd3';
import { TreemapData, TreemapNode, TreemapTile } from '../models/treemap-data';

export interface TreemapLayoutOptions {
  width: number;
  height: number;
  colors?: string[];
}

const DEFAULT_COLORS = ['#315f45', '#6f8e55', '#a9822d', '#9b5d3f', '#4e6f88', '#7a6756'];

export function computeTreemapLayout(data: TreemapData, options: TreemapLayoutOptions): TreemapTile[] {
  const root = hierarchy<TreemapNode>({
    id: '__root__',
    label: data.label,
    children: data.children,
  })
    .sum((node) => node.value ?? 0)
    .sort((left, right) => (right.value ?? 0) - (left.value ?? 0));

  const rectangularRoot = treemap<TreemapNode>()
    .tile(treemapSquarify.ratio(1.35))
    .size([options.width, options.height])
    .paddingOuter(2)
    .paddingTop((node) => node.depth === 1 ? 20 : 4)
    .paddingInner(3)
    .round(true)(root) as HierarchyRectangularNode<TreemapNode>;

  const colors = options.colors?.length ? options.colors : DEFAULT_COLORS;

  return rectangularRoot.descendants()
    .filter((node) => node.depth > 0 && !node.children)
    .map((node) => {
      const topLevel = node.ancestors().find((ancestor) => ancestor.depth === 1);
      const topLevelIndex = rectangularRoot.children?.findIndex((child) => child.data.id === topLevel?.data.id) ?? 0;
      const path = node.ancestors().reverse().slice(1).map((ancestor) => ancestor.data.label);
      return {
        id: node.data.id,
        label: node.data.label,
        value: node.value ?? 0,
        depth: node.depth,
        x: node.x0,
        y: node.y0,
        width: Math.max(0, node.x1 - node.x0),
        height: Math.max(0, node.y1 - node.y0),
        color: colors[Math.max(0, topLevelIndex) % colors.length],
        path,
        meta: node.data.meta ?? {},
      };
    });
}

export function sumTreemapValues(nodes: TreemapNode[]): number {
  return nodes.reduce((sum, node) => {
    const ownValue = node.value ?? 0;
    const childValue = node.children ? sumTreemapValues(node.children) : 0;
    return sum + ownValue + childValue;
  }, 0);
}
