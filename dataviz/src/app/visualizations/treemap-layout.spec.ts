import { TreemapData } from '../models/treemap-data';
import { computeTreemapLayout, sumTreemapValues } from './treemap-layout';

const data: TreemapData = {
  label: 'Business domains',
  metric: {
    key: 'applicationCount',
    label: 'Applications',
  },
  children: [
    {
      id: 'retail',
      label: 'Retail Banking',
      children: [
        { id: 'payments', label: 'Payments', value: 10 },
        { id: 'lending', label: 'Lending', value: 5 },
      ],
    },
    {
      id: 'wealth',
      label: 'Wealth',
      value: 3,
    },
  ],
};

describe('treemap-layout', () => {
  it('sums values recursively', () => {
    expect(sumTreemapValues(data.children)).toBe(18);
  });

  it('computes positioned leaf tiles', () => {
    const tiles = computeTreemapLayout(data, { width: 500, height: 300 });

    expect(tiles.map((tile) => tile.label).sort()).toEqual(['Lending', 'Payments', 'Wealth']);
    expect(tiles.every((tile) => tile.width > 0 && tile.height > 0)).toBe(true);
    expect(tiles.every((tile) => tile.x >= 0 && tile.y >= 0)).toBe(true);
    expect(tiles.every((tile) => tile.x + tile.width <= 500)).toBe(true);
    expect(tiles.every((tile) => tile.y + tile.height <= 300)).toBe(true);
  });
});
