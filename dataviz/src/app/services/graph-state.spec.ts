import { TestBed } from '@angular/core/testing';

import { GraphState } from './graph-state';

describe('GraphState', () => {
  let service: GraphState;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(GraphState);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
