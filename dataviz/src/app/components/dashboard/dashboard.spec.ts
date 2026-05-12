import { ComponentFixture, TestBed } from '@angular/core/testing';
import { storageFixture } from '../../../testing/fixtures/storage-fixture';
import { StorageLoaderService } from '../../services/storage-loader.service';
import { GraphState } from '../../services/graph-state';
import { Dashboard } from './dashboard';

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;
  let graphState: GraphState;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [
        {
          provide: StorageLoaderService,
          useValue: {
            loadDefault: () => Promise.resolve(storageFixture),
            loadFile: () => Promise.resolve(storageFixture),
          },
        },
      ],
    }).compileComponents();

    graphState = TestBed.inject(GraphState);
    await graphState.loadDefault();
    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('renders summary counters', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(component).toBeTruthy();
    expect(compiled.textContent).toContain('Analyse des candidats de remplacement');
    expect(compiled.textContent).toContain('Applications');
    expect(compiled.textContent).toContain('4');
    expect(compiled.textContent).toContain('APP-NARROW#Narrow App');
    expect(compiled.textContent).toContain('1.1.1#L3 A');
  });

  it('updates candidates when threshold changes', () => {
    component.thresholdPercent.set(50);
    fixture.detectChanges();

    expect(component.filteredCandidates().some((candidate) => candidate.type === 'near')).toBe(true);

    component.thresholdPercent.set(80);
    fixture.detectChanges();

    expect(component.filteredCandidates().some((candidate) => candidate.type === 'near')).toBe(false);
  });

  it('filters candidates by covered entity', () => {
    component.selectedEntity.set('E2');
    fixture.detectChanges();

    expect(component.filteredCandidates().every((candidate) => candidate.coveredEntity === 'E2')).toBe(true);
  });

  it('paginates candidates without truncating the calculated result set', () => {
    component.pageSize.set(1);
    fixture.detectChanges();

    const total = component.filteredCandidates().length;
    const firstPage = component.displayedCandidates();

    expect(total).toBeGreaterThan(1);
    expect(firstPage.length).toBe(1);

    component.nextPage();
    fixture.detectChanges();

    expect(component.pageIndex()).toBe(1);
    expect(component.displayedCandidates().length).toBe(1);
    expect(component.displayedCandidates()[0]).not.toEqual(firstPage[0]);
  });
});
