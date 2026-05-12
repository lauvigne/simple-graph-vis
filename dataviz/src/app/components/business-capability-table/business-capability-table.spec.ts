import { ComponentFixture, TestBed } from '@angular/core/testing';
import { storageFixture } from '../../../testing/fixtures/storage-fixture';
import { GraphState } from '../../services/graph-state';
import { StorageLoaderService } from '../../services/storage-loader.service';
import { BusinessCapabilityTable } from './business-capability-table';

describe('BusinessCapabilityTable', () => {
  let component: BusinessCapabilityTable;
  let fixture: ComponentFixture<BusinessCapabilityTable>;
  let graphState: GraphState;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BusinessCapabilityTable],
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
    fixture = TestBed.createComponent(BusinessCapabilityTable);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('renders one row per business capability with code and five level columns', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const headers = Array.from(compiled.querySelectorAll('th')).map((header) => header.textContent?.trim());

    expect(component.rows().length).toBe(5);
    expect(headers).toEqual(['Code', 'Niveau 1', 'Niveau 2', 'Niveau 3', 'Niveau 4', 'Niveau 5']);
    expect(compiled.textContent).toContain('1.1.1');
    expect(compiled.textContent).toContain('L3 A');
  });

  it('filters rows by code or label', () => {
    component.query.set('1.1.2');
    fixture.detectChanges();

    expect(component.filteredRows().length).toBe(1);
    expect(component.filteredRows()[0].levels).toContain('L3 B');
  });
});
