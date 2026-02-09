import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { LocationImageDialog } from './image-preview-dialog.component';

describe('LocationImageDialog', () => {
  let component: LocationImageDialog;
  let fixture: ComponentFixture<LocationImageDialog>;
  let mockDialogRef: jasmine.SpyObj<MatDialogRef<LocationImageDialog>>;

  const defaultDialogData = {
    imageUrl: 'https://example.com/image.png',
    title: 'Test Image',
  };

  beforeEach(async () => {
    mockDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      declarations: [LocationImageDialog],
      providers: [
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: defaultDialogData },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LocationImageDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('constructor', () => {
    it('should have access to dialog data', () => {
      expect(component.data).toEqual(defaultDialogData);
    });

    it('should have access to dialog ref', () => {
      expect(component.dialogRef).toBeTruthy();
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

  describe('with different dialog data', () => {
    it('should handle empty data', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [LocationImageDialog],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: {} },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(LocationImageDialog);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent).toBeTruthy();
      expect(newComponent.data).toEqual({});
    });

    it('should handle minimal data', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [LocationImageDialog],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { imgUrl: '' } },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(LocationImageDialog);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent).toBeTruthy();
      expect(newComponent.data.imgUrl).toBe('');
    });
  });
});
