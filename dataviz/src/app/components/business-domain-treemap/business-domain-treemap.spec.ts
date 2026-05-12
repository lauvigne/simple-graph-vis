import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TreemapData } from '../../models/treemap-data';
import { BusinessDomainTreemap } from './business-domain-treemap';

const fixtureData: TreemapData = {
  label: 'Business domains',
  metric: {
    key: 'applicationCount',
    label: 'Applications',
  },
  children: [
    {
      id: 'retail',
      label: 'Retail Banking',
      children: [
        { id: 'retail-payments', label: 'Payments', value: 12 },
        { id: 'retail-lending', label: 'Lending', value: 8 },
      ],
    },
    {
      id: 'wealth',
      label: 'Wealth',
      value: 5,
    },
  ],
};

describe('BusinessDomainTreemap', () => {
  let component: BusinessDomainTreemap;
  let fixture: ComponentFixture<BusinessDomainTreemap>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BusinessDomainTreemap],
    }).compileComponents();

    fixture = TestBed.createComponent(BusinessDomainTreemap);
    fixture.componentRef.setInput('data', fixtureData);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('renders the treemap title and total metric', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(component).toBeTruthy();
    expect(component.total()).toBe(25);
    expect(compiled.textContent).toContain('Business domains');
    expect(compiled.textContent).toContain('Applications');
  });

  it('creates one SVG tile per leaf node', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(component.tiles().map((tile) => tile.label).sort()).toEqual(['Lending', 'Payments', 'Wealth']);
    expect(compiled.querySelectorAll('rect').length).toBe(3);
  });
});
