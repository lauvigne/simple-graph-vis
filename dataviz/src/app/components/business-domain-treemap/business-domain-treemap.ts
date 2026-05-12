import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { TreemapData, TreemapTile } from '../../models/treemap-data';
import { computeTreemapLayout, sumTreemapValues } from '../../visualizations/treemap-layout';

@Component({
  selector: 'app-business-domain-treemap',
  imports: [DecimalPipe],
  templateUrl: './business-domain-treemap.html',
  styleUrl: './business-domain-treemap.scss',
})
export class BusinessDomainTreemap {
  readonly data = input.required<TreemapData>();
  readonly width = input(980);
  readonly height = input(520);
  readonly minTileLabelWidth = input(96);
  readonly minTileLabelHeight = input(54);

  readonly total = computed(() => sumTreemapValues(this.data().children));
  readonly tiles = computed<TreemapTile[]>(() =>
    computeTreemapLayout(this.data(), {
      width: this.width(),
      height: this.height(),
    }),
  );

  tileTitle(tile: TreemapTile): string {
    const unit = this.data().metric.unit ? ` ${this.data().metric.unit}` : '';
    return `${tile.path.join(' / ')}: ${tile.value}${unit}`;
  }

  showLabel(tile: TreemapTile): boolean {
    return tile.width >= this.minTileLabelWidth() && tile.height >= this.minTileLabelHeight();
  }
}
