import { arc, hierarchy, HierarchyRectangularNode, partition } from 'd3';
import { SunburstData, SunburstNode, SunburstSlice } from '../models/sunburst-data';

export interface SunburstLayoutOptions {
  width: number;
  height: number;
  colors?: string[];
  maxDepth?: number;
}

const DEFAULT_COLORS = ['#315f45', '#6f8e55', '#a9822d', '#9b5d3f', '#4e6f88', '#7a6756'];

export function computeSunburstLayout(data: SunburstData, options: SunburstLayoutOptions): SunburstSlice[] {
  const radius = Math.min(options.width, options.height) / 2;
  const maxDepth = options.maxDepth ?? Number.POSITIVE_INFINITY;
  const colors = options.colors?.length ? options.colors : DEFAULT_COLORS;

  const root = hierarchy<SunburstNode>({
    id: '__root__',
    label: data.label,
    children: data.children,
  })
    .sum((node) => node.value ?? 0)
    .sort((left, right) => (right.value ?? 0) - (left.value ?? 0));

  const radialRoot = partition<SunburstNode>()
    .size([2 * Math.PI, radius])
    .padding(0.003)(root) as HierarchyRectangularNode<SunburstNode>;

  const arcGenerator = arc<HierarchyRectangularNode<SunburstNode>>()
    .startAngle((node) => node.x0)
    .endAngle((node) => node.x1)
    .innerRadius((node) => node.y0)
    .outerRadius((node) => node.y1)
    .padAngle(0.0025)
    .padRadius(radius * 0.8)
    .cornerRadius(2);

  return radialRoot
    .descendants()
    .filter((node) => node.depth > 0 && node.depth <= maxDepth && (node.x1 - node.x0) > 0 && (node.y1 - node.y0) > 0)
    .map((node) => {
      const topLevel = node.ancestors().find((ancestor) => ancestor.depth === 1);
      const topLevelIndex = radialRoot.children?.findIndex((child) => child.data.id === topLevel?.data.id) ?? 0;
      const path = node.ancestors().reverse().slice(1).map((ancestor) => ancestor.data.label);
      const midAngle = (node.x0 + node.x1) / 2;
      const midRadius = (node.y0 + node.y1) / 2;
      const labelRotation = ((midAngle * 180) / Math.PI) - 90 + (midAngle > Math.PI ? 180 : 0);
      const color = colors[Math.max(0, topLevelIndex) % colors.length];
      const depthOpacity = Math.max(0.48, 0.92 - ((node.depth - 1) * 0.12));
      return {
        id: node.data.id,
        label: node.data.label,
        value: node.value ?? 0,
        depth: node.depth,
        startAngle: node.x0,
        endAngle: node.x1,
        innerRadius: node.y0,
        outerRadius: node.y1,
        angleSpan: ((node.x1 - node.x0) * 180) / Math.PI,
        ringThickness: node.y1 - node.y0,
        arcPath: arcGenerator(node) ?? '',
        color,
        opacity: depthOpacity,
        path,
        labelX: Math.cos(midAngle - Math.PI / 2) * midRadius,
        labelY: Math.sin(midAngle - Math.PI / 2) * midRadius,
        labelRotation,
        meta: node.data.meta ?? {},
      };
    });
}

export function sumSunburstValues(nodes: SunburstNode[]): number {
  return nodes.reduce((sum, node) => {
    const ownValue = node.value ?? 0;
    const childValue = node.children ? sumSunburstValues(node.children) : 0;
    return sum + ownValue + childValue;
  }, 0);
}
