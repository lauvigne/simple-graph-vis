import { CommonModule } from '@angular/common';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { CoverageCandidate, CoverageOptions, CoverageScopeMode, CoverageSummary, GraphSummary } from '../../models/storage-data';
import { CoverageAnalysisService } from '../../services/coverage-analysis.service';
import { GraphService } from '../../services/graph.service';
import { GraphState } from '../../services/graph-state';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard {
  private readonly graphService = inject(GraphService);
  private readonly coverageAnalysis = inject(CoverageAnalysisService);
  readonly graphState = inject(GraphState);

  readonly pageSizeOptions = [50, 100, 200, 500];
  readonly selectedEntity = signal('');
  readonly thresholdPercent = signal(80);
  readonly includePartialCoverage = signal(true);
  readonly scopeMode = signal<CoverageScopeMode>('all');
  readonly pageSize = signal(200);
  readonly pageIndex = signal(0);
  readonly selectedCandidate = signal<CoverageCandidate | null>(null);

  readonly graphSummary = computed<GraphSummary>(() => this.graphService.summary(this.graphState.graph()));
  readonly entities = computed(() => this.coverageAnalysis.entities(this.graphState.graph()));
  readonly candidateOptions = computed<CoverageOptions>(() => ({
    threshold: this.thresholdPercent() / 100,
    includePartialCoverage: this.includePartialCoverage(),
    maxCandidates: 5000,
    maxCandidatesPerEntity: 1250,
    entity: this.selectedEntity() || undefined,
    scopeMode: this.scopeMode(),
  }));
  readonly filteredCandidates = computed(() =>
    this.coverageAnalysis.buildCandidates(this.graphState.graph(), this.candidateOptions()),
  );
  readonly pageCount = computed(() => Math.max(1, Math.ceil(this.filteredCandidates().length / this.pageSize())));
  readonly pageStart = computed(() => this.pageIndex() * this.pageSize());
  readonly pageEnd = computed(() => Math.min(this.pageStart() + this.pageSize(), this.filteredCandidates().length));
  readonly displayedCandidates = computed(() =>
    this.filteredCandidates().slice(this.pageStart(), this.pageEnd()),
  );
  readonly coverageSummary = computed<CoverageSummary>(() =>
    this.coverageAnalysis.summarize(this.filteredCandidates()),
  );

  constructor() {
    effect(() => {
      const candidates = this.filteredCandidates();
      const current = this.selectedCandidate();
      if (!candidates.length) {
        this.selectedCandidate.set(null);
        return;
      }

      const stillPresent = current && candidates.some((candidate) =>
        candidate.coveredAppKey === current.coveredAppKey &&
        candidate.coveringAppKey === current.coveringAppKey
      );
      if (!stillPresent) {
        this.selectedCandidate.set(candidates[0]);
      }
    });

    effect(() => {
      const lastPageIndex = this.pageCount() - 1;
      if (this.pageIndex() > lastPageIndex) {
        this.pageIndex.set(lastPageIndex);
      }
    });
  }

  setEntity(event: Event): void {
    this.selectedEntity.set((event.target as HTMLSelectElement).value);
    this.resetPagination();
  }

  setThreshold(event: Event): void {
    this.thresholdPercent.set(Number((event.target as HTMLInputElement).value));
    this.resetPagination();
  }

  setIncludePartial(event: Event): void {
    this.includePartialCoverage.set((event.target as HTMLInputElement).checked);
    this.resetPagination();
  }

  setScopeMode(event: Event): void {
    this.scopeMode.set((event.target as HTMLSelectElement).value as CoverageScopeMode);
    this.resetPagination();
  }

  setPageSize(event: Event): void {
    this.pageSize.set(Number((event.target as HTMLSelectElement).value));
    this.resetPagination();
  }

  previousPage(): void {
    this.pageIndex.update((value) => Math.max(0, value - 1));
  }

  nextPage(): void {
    this.pageIndex.update((value) => Math.min(this.pageCount() - 1, value + 1));
  }

  firstPage(): void {
    this.pageIndex.set(0);
  }

  lastPage(): void {
    this.pageIndex.set(this.pageCount() - 1);
  }

  selectCandidate(candidate: CoverageCandidate): void {
    this.selectedCandidate.set(candidate);
  }

  barWidth(value: number, total: number): number {
    if (!total) return 0;
    return Math.max(4, Math.min(100, (value / total) * 100));
  }

  private resetPagination(): void {
    this.pageIndex.set(0);
  }
}
