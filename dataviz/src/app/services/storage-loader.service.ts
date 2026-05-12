import { Injectable } from '@angular/core';
import { StorageData } from '../models/storage-data';

@Injectable({ providedIn: 'root' })
export class StorageLoaderService {
  async loadDefault(): Promise<StorageData> {
    const response = await fetch('assets/storage-data.json', { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Unable to load assets/storage-data.json: HTTP ${response.status}`);
    }
    return this.parse(await response.text());
  }

  async loadFile(file: File): Promise<StorageData> {
    return this.parse(await file.text());
  }

  parse(text: string): StorageData {
    const parsed = JSON.parse(text) as StorageData;
    if (!parsed.graph || !Array.isArray(parsed.graph.nodes) || !Array.isArray(parsed.graph.edges)) {
      throw new Error('Invalid storage data: graph.nodes and graph.edges are required.');
    }
    return {
      ...parsed,
      sources: parsed.sources ?? parsed.workbooks ?? [],
      warnings: parsed.warnings ?? [],
    };
  }
}
