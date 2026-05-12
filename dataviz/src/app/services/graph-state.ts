import { computed, inject, Injectable, signal } from '@angular/core';
import { StorageData } from '../models/storage-data';
import { GraphService } from './graph.service';
import { StorageLoaderService } from './storage-loader.service';

@Injectable({
  providedIn: 'root',
})
export class GraphState {
  private readonly storageLoader = inject(StorageLoaderService);
  private readonly graphService = inject(GraphService);

  readonly storage = signal<StorageData | null>(null);
  readonly graph = signal(this.graphService.emptyGraph());
  readonly error = signal<string | null>(null);
  readonly isLoaded = computed(() => this.storage() !== null);

  async loadDefault(): Promise<void> {
    await this.load(async () => this.storageLoader.loadDefault());
  }

  async loadFile(file: File): Promise<void> {
    await this.load(async () => this.storageLoader.loadFile(file));
  }

  unload(): void {
    this.storage.set(null);
    this.graph.set(this.graphService.emptyGraph());
    this.error.set(null);
  }

  private async load(loader: () => Promise<StorageData>): Promise<void> {
    try {
      this.error.set(null);
      const storage = await loader();
      this.storage.set(storage);
      this.graph.set(this.graphService.buildGraph(storage));
    } catch (error) {
      this.error.set(error instanceof Error ? error.message : String(error));
    }
  }
}
