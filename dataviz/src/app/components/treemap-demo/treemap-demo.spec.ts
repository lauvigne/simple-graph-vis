import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TreemapDemo } from './treemap-demo';

describe('TreemapDemo', () => {
  let component: TreemapDemo;
  let fixture: ComponentFixture<TreemapDemo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TreemapDemo],
    }).compileComponents();

    fixture = TestBed.createComponent(TreemapDemo);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('renders fake application count and TCO treemaps', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('Treemap de démonstration');
    expect(compiled.textContent).toContain('Business domains - applications');
    expect(compiled.textContent).toContain('Business domains - TCO');
    expect(compiled.querySelectorAll('svg').length).toBe(2);
  });
});
