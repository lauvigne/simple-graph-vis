import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { SunburstData, SunburstSlice } from '../../models/sunburst-data';
import { computeSunburstLayout, sumSunburstValues } from '../../visualizations/sunburst-layout';

@Component({
  selector: 'app-business-capability-sunburst',
  imports: [DecimalPipe],
  templateUrl: './business-capability-sunburst.html',
  styleUrl: './business-capability-sunburst.scss',
})
export class BusinessCapabilitySunburst {
  readonly data = input<SunburstData | null>(null);
  readonly width = input(980);
  readonly height = input(560);
  readonly maxDepth = input<number | null>(null);
  readonly minLabelAngle = input(12);
  readonly minLabelThickness = input(26);

  readonly total = computed(() => {
    const data = this.data();
    return data ? sumSunburstValues(data.children) : 0;
  });
  readonly slices = computed<SunburstSlice[]>(() => {
    const data = this.data();
    return data
      ? computeSunburstLayout(data, {
          width: this.width(),
          height: this.height(),
          maxDepth: this.maxDepth() ?? undefined,
        })
      : [];
  });
  readonly centerRadius = computed(() =>
    this.slices().length ? Math.min(...this.slices().map((slice) => slice.innerRadius)) : 0,
  );

  sliceTitle(slice: SunburstSlice): string {
    const data = this.data();
    const unit = data?.metric.unit ? ` ${data.metric.unit}` : '';
    return `${slice.path.join(' / ')}: ${slice.value}${unit}`;
  }

  showLabel(slice: SunburstSlice): boolean {
    return slice.angleSpan >= this.minLabelAngle() && slice.ringThickness >= this.minLabelThickness();
  }

  visibleLabel(slice: SunburstSlice): string {
    const code = typeof slice.meta['code'] === 'string' ? slice.meta['code'].trim() : '';
    if (code) return code;
    return slice.label.split('#')[0] || slice.label;
  }

  labelTransform(slice: SunburstSlice): string {
    return `translate(${slice.labelX},${slice.labelY}) rotate(${slice.labelRotation})`;
  }
}
