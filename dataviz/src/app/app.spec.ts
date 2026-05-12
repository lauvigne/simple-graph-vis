import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { storageFixture } from '../testing/fixtures/storage-fixture';
import { App } from './app';
import { StorageLoaderService } from './services/storage-loader.service';

describe('App', () => {
  let fixture: ComponentFixture<App>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        {
          provide: StorageLoaderService,
          useValue: {
            loadDefault: () => Promise.resolve(storageFixture),
            loadFile: () => Promise.resolve(storageFixture),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('creates the application shell and renders navigation', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(fixture.componentInstance).toBeTruthy();
    expect(compiled.textContent).toContain('Coverage Dataviz');
    expect(compiled.textContent).toContain('Dashboard');
    expect(compiled.textContent).toContain('Capacités');
    expect(compiled.textContent).toContain('Chargement JSON');
  });
});
