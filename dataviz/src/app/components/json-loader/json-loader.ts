import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { GraphService } from '../../services/graph.service';
import { GraphState } from '../../services/graph-state';

@Component({
  selector: 'app-json-loader',
  imports: [CommonModule, RouterLink],
  templateUrl: './json-loader.html',
  styleUrl: './json-loader.scss',
})
export class JsonLoader {
  private readonly graphService = inject(GraphService);
  readonly graphState = inject(GraphState);
  readonly graphSummary = computed(() => this.graphService.summary(this.graphState.graph()));

  async loadDefault(): Promise<void> {
    await this.graphState.loadDefault();
  }

  async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    await this.graphState.loadFile(file);
    input.value = '';
  }

  unload(): void {
    this.graphState.unload();
  }
}
