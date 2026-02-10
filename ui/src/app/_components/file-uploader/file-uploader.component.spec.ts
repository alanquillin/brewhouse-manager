import { HttpEventType } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { DataError, DataService } from '../../_services/data.service';
import { ExtendedFile, FileUploaderComponent } from './file-uploader.component';

describe('FileUploaderComponent', () => {
  let component: FileUploaderComponent;
  let fixture: ComponentFixture<FileUploaderComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', ['uploadImage']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    await TestBed.configureTestingModule({
      declarations: [FileUploaderComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FileUploaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('default values', () => {
    it('should have empty imageType by default', () => {
      expect(component.imageType).toBe('');
    });

    it('should have allowMultiple as false by default', () => {
      expect(component.allowMultiple).toBe(false);
    });

    it('should have uploading as false by default', () => {
      expect(component.uploading).toBe(false);
    });

    it('should have empty files object by default', () => {
      expect(component.files).toEqual({});
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Upload failed');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Upload failed', 'Close');
    });
  });

  describe('onFileDropped', () => {
    it('should not process files when uploading', () => {
      component.uploading = true;
      const files = [createMockFile('test.png')];

      component.onFileDropped(files);

      expect(mockDataService.uploadImage).not.toHaveBeenCalled();
    });

    it('should display error when multiple files dropped but allowMultiple is false', () => {
      component.allowMultiple = false;
      const files = [createMockFile('test1.png'), createMockFile('test2.png')];

      component.onFileDropped(files);

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error: Mutli-file uploads are disabled.',
        'Close'
      );
    });

    it('should call uploadFiles when single file dropped', () => {
      spyOn(component, 'uploadFiles');
      const files = [createMockFile('test.png')];

      component.onFileDropped(files);

      expect(component.uploadFiles).toHaveBeenCalledWith(files);
    });

    it('should call uploadFiles with multiple files when allowMultiple is true', () => {
      component.allowMultiple = true;
      spyOn(component, 'uploadFiles');
      const files = [createMockFile('test1.png'), createMockFile('test2.png')];

      component.onFileDropped(files);

      expect(component.uploadFiles).toHaveBeenCalledWith(files);
    });
  });

  describe('fileBrowseHandler', () => {
    it('should not process when uploading', () => {
      component.uploading = true;

      component.fileBrowseHandler({ target: { files: [createMockFile('test.png')] } });

      expect(mockDataService.uploadImage).not.toHaveBeenCalled();
    });

    it('should not process when event is null', () => {
      component.fileBrowseHandler(null);

      expect(mockDataService.uploadImage).not.toHaveBeenCalled();
    });

    it('should upload files from file input', () => {
      mockDataService.uploadImage.and.returnValue(
        of({ type: HttpEventType.Response, destinationPath: '/path' })
      );

      component.fileBrowseHandler({ target: { files: [createMockFile('test.png')] } });

      expect(mockDataService.uploadImage).toHaveBeenCalled();
    });
  });

  describe('areUploadsComplete', () => {
    it('should return true when files object is empty', () => {
      component.files = {};

      expect(component.areUploadsComplete()).toBe(true);
    });

    it('should return true when all files have progress 100', () => {
      component.files = {
        'file1.png': createExtendedFile('file1.png', 100),
        'file2.png': createExtendedFile('file2.png', 100),
      };

      expect(component.areUploadsComplete()).toBe(true);
    });

    it('should return false when any file has progress less than 100', () => {
      component.files = {
        'file1.png': createExtendedFile('file1.png', 100),
        'file2.png': createExtendedFile('file2.png', 50),
      };

      expect(component.areUploadsComplete()).toBe(false);
    });

    it('should include failures when includeFailures is true', () => {
      const failedFile = createExtendedFile('file2.png', 0);
      failedFile.hasError = true;
      component.files = {
        'file1.png': createExtendedFile('file1.png', 100),
        'file2.png': failedFile,
      };

      expect(component.areUploadsComplete(true)).toBe(true);
    });

    it('should not include failures when includeFailures is false', () => {
      const failedFile = createExtendedFile('file2.png', 0);
      failedFile.hasError = true;
      component.files = {
        'file1.png': createExtendedFile('file1.png', 100),
        'file2.png': failedFile,
      };

      expect(component.areUploadsComplete(false)).toBe(false);
    });
  });

  describe('upload', () => {
    it('should update progress on UploadProgress event', () => {
      const file = createExtendedFile('test.png', 0);
      mockDataService.uploadImage.and.returnValue(
        of({
          type: HttpEventType.UploadProgress,
          loaded: 50,
          total: 100,
        })
      );

      component.upload(file);

      expect(file.progress).toBe(50);
    });

    it('should set progress to 100 and path on complete', () => {
      const file = createExtendedFile('test.png', 0);
      mockDataService.uploadImage.and.returnValue(
        of({
          type: HttpEventType.Response,
          destinationPath: '/uploads/test.png',
        })
      );

      component.upload(file);

      expect(file.progress).toBe(100);
      expect(file.path).toBe('/uploads/test.png');
    });

    it('should emit uploadComplete on successful upload', () => {
      const file = createExtendedFile('test.png', 0);
      mockDataService.uploadImage.and.returnValue(
        of({
          type: HttpEventType.Response,
          destinationPath: '/uploads/test.png',
        })
      );
      spyOn(component.uploadComplete, 'emit');

      component.upload(file);

      expect(component.uploadComplete.emit).toHaveBeenCalledWith(file);
    });

    it('should set hasError and errorMessage on error', () => {
      const file = createExtendedFile('test.png', 50);
      const error: DataError = { message: 'Upload failed' } as DataError;
      mockDataService.uploadImage.and.returnValue(throwError(() => error));

      component.upload(file);

      expect(file.progress).toBe(0);
      expect(file.hasError).toBe(true);
      expect(file.errorMessage).toBe('Upload failed');
    });

    it('should set uploading to false on error when not allowMultiple', () => {
      component.uploading = true;
      component.allowMultiple = false;
      const file = createExtendedFile('test.png', 50);
      const error: DataError = { message: 'Upload failed' } as DataError;
      mockDataService.uploadImage.and.returnValue(throwError(() => error));

      component.upload(file);

      expect(component.uploading).toBe(false);
    });
  });

  describe('uploadFiles', () => {
    it('should set uploading to true', () => {
      mockDataService.uploadImage.and.returnValue(
        of({ type: HttpEventType.Response, destinationPath: '/path' })
      );
      const files = [createMockFile('test.png')];

      component.uploadFiles(files);

      expect(component.uploading).toBe(true);
    });

    it('should clear existing files', () => {
      component.files = { 'old.png': createExtendedFile('old.png', 100) };
      mockDataService.uploadImage.and.returnValue(
        of({ type: HttpEventType.Response, destinationPath: '/path' })
      );
      const files = [createMockFile('new.png')];

      component.uploadFiles(files);

      expect(component.files['old.png']).toBeUndefined();
    });

    it('should skip duplicate file names', () => {
      mockDataService.uploadImage.and.returnValue(
        of({ type: HttpEventType.Response, destinationPath: '/path' })
      );
      const files = [createMockFile('test.png'), createMockFile('test.png')];

      component.uploadFiles(files);

      expect(mockDataService.uploadImage).toHaveBeenCalledTimes(1);
    });

    it('should add files to the files object', () => {
      mockDataService.uploadImage.and.returnValue(
        of({ type: HttpEventType.Response, destinationPath: '/path' })
      );
      const files = [createMockFile('test.png')];

      component.uploadFiles(files);

      expect(component.files['test.png']).toBeDefined();
    });
  });

  describe('formatBytes', () => {
    it('should return "0 Bytes" for 0 bytes', () => {
      expect(component.formatBytes(0)).toBe('0 Bytes');
    });

    it('should format bytes correctly', () => {
      expect(component.formatBytes(500)).toBe('500 Bytes');
    });

    it('should format kilobytes correctly', () => {
      expect(component.formatBytes(1024)).toBe('1 KB');
    });

    it('should format megabytes correctly', () => {
      expect(component.formatBytes(1048576)).toBe('1 MB');
    });

    it('should format gigabytes correctly', () => {
      expect(component.formatBytes(1073741824)).toBe('1 GB');
    });

    it('should respect decimal places', () => {
      expect(component.formatBytes(1536, 1)).toBe('1.5 KB');
    });

    it('should handle zero decimal places', () => {
      expect(component.formatBytes(1536, 0)).toBe('2 KB');
    });

    it('should default to 2 decimal places', () => {
      expect(component.formatBytes(1536)).toBe('1.5 KB');
    });
  });
});

function createMockFile(name: string): File {
  return new File(['content'], name, { type: 'image/png' });
}

function createExtendedFile(name: string, progress: number): ExtendedFile {
  const file = new File(['content'], name, { type: 'image/png' }) as ExtendedFile;
  file.progress = progress;
  file.hasError = false;
  file.errorMessage = undefined;
  file.path = undefined;
  return file;
}
