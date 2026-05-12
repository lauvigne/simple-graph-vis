import { beforeEach, describe, expect, it } from 'vitest';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { storageFixture } from '../../../testing/fixtures/storage-fixture';
import { GraphState } from '../../services/graph-state';
import { StorageLoaderService } from '../../services/storage-loader.service';
import { SunburstDemo } from './sunburst-demo';

describe('SunburstDemo', () => {
  let component: SunburstDemo;
  let fixture: ComponentFixture<SunburstDemo>;
  let graphState: GraphState;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SunburstDemo],
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
    fixture = TestBed.createComponent(SunburstDemo);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('renders the two demo sunbursts', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('Sunburst de démonstration');
    expect(compiled.textContent).toContain('Business capabilities - niveaux 1 et 2');
    expect(compiled.textContent).toContain('Business capabilities - TCO simulé');
    expect(compiled.textContent).toContain('1#L1');
    expect(compiled.textContent).toContain('1.1#L2');
    expect(compiled.querySelectorAll('svg').length).toBe(2);
  });
});
