import { TestBed } from '@angular/core/testing';
import { storageFixture } from '../../testing/fixtures/storage-fixture';
import { GraphService } from './graph.service';

describe('GraphService', () => {
  let service: GraphService;

  beforeEach(() => {
    service = TestBed.inject(GraphService);
  });

  it('rebuilds nodes, edges, and indexes by kind', () => {
    const graph = service.buildGraph(storageFixture);

    expect(graph.nodes.size).toBe(11);
    expect(graph.edges.length).toBe(13);
    expect(service.nodesByKind(graph, 'application').length).toBe(4);
    expect(service.nodesByKind(graph, 'entity').map((node) => node.label)).toEqual(['E1', 'E2']);
  });

  it('computes descendant closure through contains edges', () => {
    const graph = service.buildGraph(storageFixture);
    const closure = service.closure(graph, ['businessCapacity:l2']);

    expect(Array.from(closure).sort()).toEqual([
      'businessCapacity:l2',
      'businessCapacity:l3a',
      'businessCapacity:l3b',
      'businessCapacity:l3c',
    ]);
  });
});
