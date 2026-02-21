import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { LocationQRCodeDialogComponent } from './qrcode-dialog.component';

describe('LocationQRCodeDialog', () => {
  let component: LocationQRCodeDialogComponent;
  let fixture: ComponentFixture<LocationQRCodeDialogComponent>;
  let mockDialogRef: jasmine.SpyObj<MatDialogRef<LocationQRCodeDialogComponent>>;

  const defaultDialogData = {
    url: 'https://example.com/location/123',
    title: 'My Location',
    width: 400,
  };

  beforeEach(async () => {
    mockDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      declarations: [LocationQRCodeDialogComponent],
      providers: [
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: defaultDialogData },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LocationQRCodeDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('constructor', () => {
    it('should set url from dialog data', () => {
      expect(component.url).toBe('https://example.com/location/123');
    });

    it('should set title from dialog data', () => {
      expect(component.title).toBe('My Location');
    });

    it('should set width from dialog data', () => {
      expect(component.width).toBe(400);
    });
  });

  describe('with default values', () => {
    it('should default title to empty string when not provided', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [LocationQRCodeDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { url: 'https://test.com' } },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(LocationQRCodeDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.title).toBe('');
    });

    it('should default width to 600 when not provided', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [LocationQRCodeDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { url: 'https://test.com' } },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(LocationQRCodeDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.width).toBe(600);
    });

    it('should convert string width to integer', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [LocationQRCodeDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { url: 'https://test.com', width: '350' } },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(LocationQRCodeDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.width).toBe(350);
    });
  });

  describe('onClick', () => {
    it('should close the dialog', () => {
      component.onClick();

      expect(mockDialogRef.close).toHaveBeenCalled();
    });

    it('should close dialog without passing any data', () => {
      component.onClick();

      expect(mockDialogRef.close).toHaveBeenCalledWith();
    });
  });

  describe('isNilOrEmpty helper', () => {
    it('should be available as a function', () => {
      expect(typeof component.isNilOrEmpty).toBe('function');
    });

    it('should return true for null', () => {
      expect(component.isNilOrEmpty(null)).toBe(true);
    });

    it('should return true for undefined', () => {
      expect(component.isNilOrEmpty(undefined)).toBe(true);
    });

    it('should return true for empty string', () => {
      expect(component.isNilOrEmpty('')).toBe(true);
    });

    it('should return false for non-empty string', () => {
      expect(component.isNilOrEmpty('test')).toBe(false);
    });
  });
});
