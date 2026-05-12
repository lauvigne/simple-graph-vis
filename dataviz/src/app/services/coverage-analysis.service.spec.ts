import { TestBed } from '@angular/core/testing';
import { storageFixture } from '../../testing/fixtures/storage-fixture';
import { CoverageAnalysisService } from './coverage-analysis.service';
import { GraphService } from './graph.service';

describe('CoverageAnalysisService', () => {
  let graphService: GraphService;
  let service: CoverageAnalysisService;

  beforeEach(() => {
    graphService = TestBed.inject(GraphService);
    service = TestBed.inject(CoverageAnalysisService);
  });

  it('detects that an L2 mapping covers applications mapped to child L3 capabilities', () => {
    const graph = graphService.buildGraph(storageFixture);
    const candidates = service.buildCandidates(graph, {
      threshold: 0.8,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
    });

    expect(candidates).toContainEqual(expect.objectContaining({
      entity: 'E1',
      coveredApp: 'Narrow App',
      coveringApp: 'Wide App',
      coveredAppCode: 'APP-NARROW',
      coveringAppCode: 'APP-WIDE',
      type: 'exact',
      coverage: 1,
    }));
  });

  it('keeps near coverage above the threshold and ignores lower coverage', () => {
    const graph = graphService.buildGraph(storageFixture);
    const candidates = service.buildCandidates(graph, {
      threshold: 0.5,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
    });

    expect(candidates).toContainEqual(expect.objectContaining({
      coveredApp: 'Wide App',
      coveringApp: 'Partial App',
      type: 'near',
    }));

    const strictCandidates = service.buildCandidates(graph, {
      threshold: 0.8,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
    });
    expect(strictCandidates).not.toContainEqual(expect.objectContaining({
      coveredApp: 'Wide App',
      coveringApp: 'Partial App',
    }));
  });

  it('isolates candidates by entity', () => {
    const graph = graphService.buildGraph(storageFixture);
    const candidates = service.buildCandidates(graph, {
      threshold: 0.5,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
      entity: 'E2',
    });

    expect(candidates.every((candidate) => candidate.entity === 'E2')).toBe(true);
  });

  it('compares all entities by default and can restrict to cross-entity candidates', () => {
    const graph = graphService.buildGraph(storageFixture);
    const defaultCandidates = service.buildCandidates(graph, {
      threshold: 0.8,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
    });

    expect(defaultCandidates).toContainEqual(expect.objectContaining({
      coveredEntity: 'E1',
      coveringEntity: 'E2',
      coveredApp: 'Narrow App',
      coveringApp: 'Other Entity App',
      type: 'exact',
    }));

    const crossEntityCandidates = service.buildCandidates(graph, {
      threshold: 0.8,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
      scopeMode: 'crossEntity',
    });

    expect(crossEntityCandidates.length).toBeGreaterThan(0);
    expect(crossEntityCandidates.every((candidate) => candidate.coveredEntity !== candidate.coveringEntity)).toBe(true);
  });

  it('summarizes relations separately from distinct applications', () => {
    const graph = graphService.buildGraph(storageFixture);
    const candidates = service.buildCandidates(graph, {
      threshold: 0.5,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
      scopeMode: 'withinEntity',
    });

    const summary = service.summarize(candidates);

    expect(summary.candidates).toBe(candidates.length);
    expect(summary.exact + summary.near).toBe(candidates.length);
    expect(summary.coveredApplications).toBeLessThanOrEqual(summary.candidates);
    expect(summary.coveringApplications).toBeLessThanOrEqual(summary.candidates);
  });

  it('does not reduce covered applications when the near threshold is lowered', () => {
    const graph = graphService.buildGraph(storageFixture);
    const strictCandidates = service.buildCandidates(graph, {
      threshold: 0.8,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
      maxCandidatesPerCoveredApplication: 20,
      scopeMode: 'withinEntity',
    });
    const relaxedCandidates = service.buildCandidates(graph, {
      threshold: 0.5,
      includePartialCoverage: true,
      maxCandidates: 20,
      maxCandidatesPerEntity: 20,
      maxCandidatesPerCoveredApplication: 20,
      scopeMode: 'withinEntity',
    });

    expect(service.summarize(relaxedCandidates).coveredApplications)
      .toBeGreaterThanOrEqual(service.summarize(strictCandidates).coveredApplications);
  });
});
