import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { ExtendedFile } from '../../_components/file-uploader/file-uploader.component';
import { FileUploadDialogComponent } from './file-upload-dialog.component';

describe('FileUploadDialogComponent', () => {
  let component: FileUploadDialogComponent;
  let fixture: ComponentFixture<FileUploadDialogComponent>;
  let mockDialogRef: jasmine.SpyObj<MatDialogRef<FileUploadDialogComponent>>;

  const defaultDialogData = {
    imageType: 'beer',
    allowMultiple: false,
    closeOnComplete: true,
  };

  beforeEach(async () => {
    mockDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      declarations: [FileUploadDialogComponent],
      providers: [
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: defaultDialogData },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FileUploadDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('constructor', () => {
    it('should set imageType from dialog data', () => {
      expect(component.imageType).toBe('beer');
    });

    it('should set allowMultiple from dialog data', () => {
      expect(component.allowMultiple).toBe(false);
    });

    it('should set closeOnComplete from dialog data', () => {
      expect(component.closeOnComplete).toBe(true);
    });
  });

  describe('with different dialog data', () => {
    it('should handle allowMultiple as true', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [FileUploadDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          {
            provide: MAT_DIALOG_DATA,
            useValue: { imageType: 'location', allowMultiple: true, closeOnComplete: false },
          },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(FileUploadDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.imageType).toBe('location');
      expect(newComponent.allowMultiple).toBe(true);
      expect(newComponent.closeOnComplete).toBe(false);
    });

    it('should default allowMultiple to false when not provided', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [FileUploadDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { imageType: 'test' } },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(FileUploadDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.allowMultiple).toBe(false);
    });

    it('should default closeOnComplete to true when not provided', async () => {
      await TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        declarations: [FileUploadDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { imageType: 'test' } },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(FileUploadDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.closeOnComplete).toBe(true);
    });
  });

  describe('onUploadComplete', () => {
    it('should be callable with a file', () => {
      const mockFile = new File([''], 'test.png', { type: 'image/png' }) as ExtendedFile;
      expect(() => component.onUploadComplete(mockFile)).not.toThrow();
    });
  });

  describe('onAllUploadsComplete', () => {
    it('should close dialog with files when closeOnComplete is true', () => {
      component.closeOnComplete = true;
      const mockFiles = [
        new File([''], 'test1.png', { type: 'image/png' }) as ExtendedFile,
        new File([''], 'test2.png', { type: 'image/png' }) as ExtendedFile,
      ];

      component.onAllUploadsComplete(mockFiles);

      expect(mockDialogRef.close).toHaveBeenCalledWith(mockFiles);
    });

    it('should not close dialog when closeOnComplete is false', () => {
      component.closeOnComplete = false;
      const mockFiles = [new File([''], 'test.png', { type: 'image/png' }) as ExtendedFile];

      component.onAllUploadsComplete(mockFiles);

      expect(mockDialogRef.close).not.toHaveBeenCalled();
    });
  });
});
