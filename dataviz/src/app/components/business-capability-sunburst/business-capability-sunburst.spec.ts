import { beforeEach, describe, expect, it } from 'vitest';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SunburstData } from '../../models/sunburst-data';
import { BusinessCapabilitySunburst } from './business-capability-sunburst';

const fixtureData: SunburstData = {
  label: 'Business capabilities',
  metric: {
    key: 'capabilityCount',
    label: 'Capabilities',
  },
  children: [
    {
      id: 'customer',
      label: 'Customer',
      children: [
        {
          id: 'journey',
          label: 'Journey',
          children: [
            { id: 'onboarding', label: 'Onboarding', value: 1 },
            { id: 'servicing', label: 'Servicing', value: 1 },
          ],
        },
      ],
    },
    {
      id: 'payments',
      label: 'Payments',
      children: [
        {
          id: 'core',
          label: 'Core',
          children: [
            { id: 'sepa', label: 'SEPA', value: 2 },
          ],
        },
      ],
    },
  ],
};

describe('BusinessCapabilitySunburst', () => {
  let component: BusinessCapabilitySunburst;
  let fixture: ComponentFixture<BusinessCapabilitySunburst>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BusinessCapabilitySunburst],
    }).compileComponents();

    fixture = TestBed.createComponent(BusinessCapabilitySunburst);
    fixture.componentRef.setInput('data', fixtureData);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it('renders the title and total metric', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(component.total()).toBe(4);
    expect(compiled.textContent).toContain('Business capabilities');
    expect(compiled.textContent).toContain('Capabilities');
  });

  it('renders one arc per visible node', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(component.slices().map((slice) => slice.label).sort()).toEqual([
      'Core',
      'Customer',
      'Journey',
      'Onboarding',
      'Payments',
      'SEPA',
      'Servicing',
    ].sort());
    expect(compiled.querySelectorAll('path').length).toBe(7);
    expect(compiled.querySelectorAll('svg').length).toBe(1);
  });

  it('uses only the code as the visible arc label and keeps the full tooltip', () => {
    const codedSlice = {
      ...component.slices()[0],
      label: '1.1#Payments',
      path: ['1#Root', '1.1#Payments'],
      meta: { code: '1.1' },
    };

    expect(component.visibleLabel(codedSlice)).toBe('1.1');
    expect(component.sliceTitle(codedSlice)).toBe(`1#Root / 1.1#Payments: ${codedSlice.value}`);
  });

  it('shows an empty state when no data is present', async () => {
    const emptyFixture = TestBed.createComponent(BusinessCapabilitySunburst);
    emptyFixture.detectChanges();
    await emptyFixture.whenStable();

    expect((emptyFixture.nativeElement as HTMLElement).textContent).toContain('Aucune donnée de sunburst à afficher.');
  });
});
