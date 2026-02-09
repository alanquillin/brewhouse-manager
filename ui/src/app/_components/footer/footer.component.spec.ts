import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { FooterComponent } from './footer.component';
import { environment } from '../../../environments/environment';

describe('FooterComponent', () => {
  let component: FooterComponent;
  let fixture: ComponentFixture<FooterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [FooterComponent],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FooterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('appVersion', () => {
    it('should be set from environment', () => {
      expect(component.appVersion).toBe(environment.appVersion);
    });

    it('should be defined', () => {
      expect(component.appVersion).toBeDefined();
    });

    it('should be a string', () => {
      expect(typeof component.appVersion).toBe('string');
    });
  });

  describe('ngOnInit', () => {
    it('should be callable', () => {
      expect(() => component.ngOnInit()).not.toThrow();
    });
  });

  describe('template rendering', () => {
    it('should render component', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled).toBeTruthy();
    });
  });
});
