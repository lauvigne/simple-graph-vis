import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { JsonLoader } from './json-loader';

describe('JsonLoader', () => {
  let component: JsonLoader;
  let fixture: ComponentFixture<JsonLoader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [JsonLoader],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(JsonLoader);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
