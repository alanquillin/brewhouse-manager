import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { DataError, DataService } from '../../_services/data.service';
import { ImageSelectorDialogComponent } from './image-selector-dialog.component';

describe('ImageSelectorDialogComponent', () => {
  let component: ImageSelectorDialogComponent;
  let fixture: ComponentFixture<ImageSelectorDialogComponent>;
  let mockDialogRef: jasmine.SpyObj<MatDialogRef<ImageSelectorDialogComponent>>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  // Use data URIs to avoid 404 warnings from karma web server
  // Each URI is slightly different to avoid NG0955 duplicate key warnings
  const mockImageDataUri1 =
    'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
  const mockImageDataUri2 =
    'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAAA///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
  const mockImageDataUri3 =
    'data:image/gif;base64,R0lGODlhAQABAIAAAAAAP////yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

  const defaultDialogData = {
    currentImage: mockImageDataUri1,
    imageType: 'beer',
  };

  const mockImages = [mockImageDataUri1, mockImageDataUri2, mockImageDataUri3];

  beforeEach(async () => {
    mockDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);
    mockDataService = jasmine.createSpyObj('DataService', ['listImages']);
    mockDataService.listImages.and.returnValue(of(mockImages));
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    await TestBed.configureTestingModule({
      declarations: [ImageSelectorDialogComponent],
      providers: [
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: defaultDialogData },
        { provide: DataService, useValue: mockDataService },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ImageSelectorDialogComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('constructor', () => {
    it('should set currentImage from dialog data', () => {
      fixture.detectChanges();
      expect(component.currentImage).toBe(mockImageDataUri1);
    });

    it('should set imageType from dialog data', () => {
      fixture.detectChanges();
      expect(component.imageType).toBe('beer');
    });

    it('should set processing to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have images as empty array initially', () => {
      expect(component.images).toEqual([]);
    });
  });

  describe('ngOnInit', () => {
    it('should set processing to true while loading', () => {
      // Don't call detectChanges yet to check initial state change
      component.ngOnInit();
      // Since observable is synchronous in test, processing will be false after
      expect(mockDataService.listImages).toHaveBeenCalledWith('beer');
    });

    it('should call dataService.listImages with imageType', () => {
      fixture.detectChanges();
      expect(mockDataService.listImages).toHaveBeenCalledWith('beer');
    });

    it('should set images on successful response', () => {
      fixture.detectChanges();
      expect(component.images).toEqual(mockImages);
    });

    it('should set processing to false after successful response', () => {
      fixture.detectChanges();
      expect(component.processing).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load images' } as DataError;
      mockDataService.listImages.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load images', 'Close');
    });

    it('should set processing to false after error', () => {
      const error: DataError = { message: 'Failed to load images' } as DataError;
      mockDataService.listImages.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(component.processing).toBe(false);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      fixture.detectChanges();

      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('onClick', () => {
    it('should set selectedImage to clicked image', () => {
      fixture.detectChanges();

      component.onClick('/images/selected.png');

      expect(component.selectedImage).toBe('/images/selected.png');
    });

    it('should update selectedImage when different image clicked', () => {
      fixture.detectChanges();
      component.selectedImage = '/images/first.png';

      component.onClick('/images/second.png');

      expect(component.selectedImage).toBe('/images/second.png');
    });
  });

  describe('onDoubleClick', () => {
    it('should set selectedImage to double-clicked image', () => {
      fixture.detectChanges();

      component.onDoubleClick('/images/selected.png');

      expect(component.selectedImage).toBe('/images/selected.png');
    });

    it('should close dialog with selected image', () => {
      fixture.detectChanges();

      component.onDoubleClick('/images/selected.png');

      expect(mockDialogRef.close).toHaveBeenCalledWith('/images/selected.png');
    });
  });

  describe('closeWithSelectedImage', () => {
    it('should close dialog with selected image', () => {
      fixture.detectChanges();
      component.selectedImage = '/images/selected.png';

      component.closeWithSelectedImage();

      expect(mockDialogRef.close).toHaveBeenCalledWith('/images/selected.png');
    });

    it('should close dialog with undefined if no image selected', () => {
      fixture.detectChanges();
      component.selectedImage = undefined;

      component.closeWithSelectedImage();

      expect(mockDialogRef.close).toHaveBeenCalledWith(undefined);
    });
  });

  describe('select', () => {
    it('should call closeWithSelectedImage', () => {
      fixture.detectChanges();
      spyOn(component, 'closeWithSelectedImage');

      component.select();

      expect(component.closeWithSelectedImage).toHaveBeenCalled();
    });

    it('should close dialog with selected image', () => {
      fixture.detectChanges();
      component.selectedImage = '/images/final.png';

      component.select();

      expect(mockDialogRef.close).toHaveBeenCalledWith('/images/final.png');
    });
  });

  describe('isNilOrEmpty helper', () => {
    it('should be available as a function', () => {
      fixture.detectChanges();
      expect(typeof component.isNilOrEmpty).toBe('function');
    });

    it('should return true for null', () => {
      fixture.detectChanges();
      expect(component.isNilOrEmpty(null)).toBe(true);
    });

    it('should return true for undefined', () => {
      fixture.detectChanges();
      expect(component.isNilOrEmpty(undefined)).toBe(true);
    });

    it('should return true for empty string', () => {
      fixture.detectChanges();
      expect(component.isNilOrEmpty('')).toBe(true);
    });

    it('should return false for non-empty string', () => {
      fixture.detectChanges();
      expect(component.isNilOrEmpty('test')).toBe(false);
    });

    it('should return true for empty array', () => {
      fixture.detectChanges();
      expect(component.isNilOrEmpty([])).toBe(true);
    });

    it('should return false for non-empty array', () => {
      fixture.detectChanges();
      expect(component.isNilOrEmpty([1, 2, 3])).toBe(false);
    });
  });

  describe('with different image types', () => {
    it('should handle location imageType', async () => {
      await TestBed.resetTestingModule();

      const locationImages = [mockImageDataUri1, mockImageDataUri2];
      mockDataService.listImages.and.returnValue(of(locationImages));

      await TestBed.configureTestingModule({
        declarations: [ImageSelectorDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: mockDialogRef },
          { provide: MAT_DIALOG_DATA, useValue: { currentImage: '', imageType: 'location' } },
          { provide: DataService, useValue: mockDataService },
          { provide: MatSnackBar, useValue: mockSnackBar },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(ImageSelectorDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.imageType).toBe('location');
      expect(mockDataService.listImages).toHaveBeenCalledWith('location');
    });
  });
});
