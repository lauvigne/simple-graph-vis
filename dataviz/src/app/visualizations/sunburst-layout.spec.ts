import { describe, expect, it } from 'vitest';
import { SunburstData } from '../models/sunburst-data';
import { computeSunburstLayout, sumSunburstValues } from './sunburst-layout';

const data: SunburstData = {
  label: 'Business capabilities',
  metric: {
    key: 'capabilityCount',
    label: 'Capabilities',
  },
  children: [
    {
      id: 'customer',
      label: 'Customer',
      children: [
        {
          id: 'journey',
          label: 'Journey',
          children: [
            { id: 'onboarding', label: 'Onboarding', value: 1 },
            { id: 'servicing', label: 'Servicing', value: 1 },
          ],
        },
      ],
    },
    {
      id: 'payments',
      label: 'Payments',
      children: [
        {
          id: 'core',
          label: 'Core',
          children: [
            { id: 'sepa', label: 'SEPA', value: 2 },
          ],
        },
      ],
    },
  ],
};

describe('sunburst-layout', () => {
  it('sums values recursively', () => {
    expect(sumSunburstValues(data.children)).toBe(4);
  });

  it('computes bounded arcs and labels', () => {
    const slices = computeSunburstLayout(data, { width: 640, height: 480 });

    expect(slices.map((slice) => slice.label).sort()).toEqual([
      'Core',
      'Customer',
      'Journey',
      'Onboarding',
      'Payments',
      'SEPA',
      'Servicing',
    ].sort());
    expect(slices.every((slice) => slice.startAngle >= 0 && slice.endAngle <= Math.PI * 2)).toBe(true);
    expect(slices.every((slice) => slice.innerRadius >= 0 && slice.outerRadius <= 240)).toBe(true);
    expect(slices.every((slice) => slice.arcPath.length > 0)).toBe(true);
  });
});
