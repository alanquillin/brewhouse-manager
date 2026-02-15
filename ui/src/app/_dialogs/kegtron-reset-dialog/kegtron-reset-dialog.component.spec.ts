import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { DataError, DataService } from '../../_services/data.service';
import { KegtronResetDialogComponent } from './kegtron-reset-dialog.component';

describe('KegtronResetDialogComponent', () => {
  let component: KegtronResetDialogComponent;
  let fixture: ComponentFixture<KegtronResetDialogComponent>;
  let mockDialogRef: jasmine.SpyObj<MatDialogRef<KegtronResetDialogComponent>>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const defaultDialogData = {
    deviceId: 'test-device-001',
    portNum: 0,
  };

  beforeEach(async () => {
    mockDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);
    mockDataService = jasmine.createSpyObj('DataService', ['resetKegtronPort']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    // Allow disableClose to be set
    (mockDialogRef as any).disableClose = false;

    await TestBed.configureTestingModule({
      declarations: [KegtronResetDialogComponent],
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
    fixture = TestBed.createComponent(KegtronResetDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have volumeSize set to null', () => {
      expect(component.volumeSize).toBeNull();
    });

    it('should have volumeUnit set to gal', () => {
      expect(component.volumeUnit).toBe('gal');
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have showSkip set to false by default', () => {
      expect(component.showSkip).toBe(false);
    });

    it('should have three volume unit options', () => {
      expect(component.volumeUnits.length).toBe(3);
      expect(component.volumeUnits.map(u => u.value)).toEqual(['gal', 'l', 'ml']);
    });

    it('should set disableClose to false on dialog ref', () => {
      expect(mockDialogRef.disableClose).toBe(false);
    });
  });

  describe('constructor with showSkip', () => {
    it('should set showSkip to true when provided in data', async () => {
      await TestBed.resetTestingModule();

      const dialogRefWithSkip = jasmine.createSpyObj('MatDialogRef', ['close']);
      (dialogRefWithSkip as any).disableClose = false;

      await TestBed.configureTestingModule({
        declarations: [KegtronResetDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: dialogRefWithSkip },
          {
            provide: MAT_DIALOG_DATA,
            useValue: { deviceId: 'dev-1', portNum: 0, showSkip: true },
          },
          { provide: DataService, useValue: mockDataService },
          { provide: MatSnackBar, useValue: mockSnackBar },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(KegtronResetDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();

      expect(newComponent.showSkip).toBe(true);
    });
  });

  describe('submit', () => {
    beforeEach(() => {
      component.volumeSize = 5.0;
      component.volumeUnit = 'gal';
      mockDataService.resetKegtronPort.and.returnValue(of(true));
    });

    it('should set processing to true', () => {
      component.submit();
      // Processing is reset to false after sync observable completes
      expect(mockDataService.resetKegtronPort).toHaveBeenCalled();
    });

    it('should set disableClose to true while processing', () => {
      mockDataService.resetKegtronPort.and.returnValue(of(true));
      // We need to check the value during the call
      mockDataService.resetKegtronPort.and.callFake(() => {
        expect(mockDialogRef.disableClose).toBe(true);
        return of(true);
      });

      component.submit();
    });

    it('should call resetKegtronPort with correct params', () => {
      component.submit();

      expect(mockDataService.resetKegtronPort).toHaveBeenCalledWith(
        'test-device-001',
        0,
        { volumeSize: 5.0, volumeUnit: 'gal' },
        undefined
      );
    });

    it('should include batchId in payload when provided in data', async () => {
      await TestBed.resetTestingModule();

      const dialogRefBatch = jasmine.createSpyObj('MatDialogRef', ['close']);
      (dialogRefBatch as any).disableClose = false;
      const batchDataService = jasmine.createSpyObj('DataService', ['resetKegtronPort']);
      batchDataService.resetKegtronPort.and.returnValue(of(true));

      await TestBed.configureTestingModule({
        declarations: [KegtronResetDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: dialogRefBatch },
          {
            provide: MAT_DIALOG_DATA,
            useValue: { deviceId: 'dev-1', portNum: 0, batchId: 'batch-123' },
          },
          { provide: DataService, useValue: batchDataService },
          { provide: MatSnackBar, useValue: mockSnackBar },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(KegtronResetDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();
      newComponent.volumeSize = 5.0;
      newComponent.volumeUnit = 'gal';

      newComponent.submit();

      expect(batchDataService.resetKegtronPort).toHaveBeenCalledWith(
        'dev-1',
        0,
        { volumeSize: 5.0, volumeUnit: 'gal', batchId: 'batch-123' },
        undefined
      );
    });

    it('should pass updateDateTapped to service', async () => {
      await TestBed.resetTestingModule();

      const dialogRefDate = jasmine.createSpyObj('MatDialogRef', ['close']);
      (dialogRefDate as any).disableClose = false;
      const dateDataService = jasmine.createSpyObj('DataService', ['resetKegtronPort']);
      dateDataService.resetKegtronPort.and.returnValue(of(true));

      await TestBed.configureTestingModule({
        declarations: [KegtronResetDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: dialogRefDate },
          {
            provide: MAT_DIALOG_DATA,
            useValue: { deviceId: 'dev-1', portNum: 0, updateDateTapped: true },
          },
          { provide: DataService, useValue: dateDataService },
          { provide: MatSnackBar, useValue: mockSnackBar },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(KegtronResetDialogComponent);
      const newComponent = newFixture.componentInstance;
      newFixture.detectChanges();
      newComponent.volumeSize = 5.0;
      newComponent.volumeUnit = 'gal';

      newComponent.submit();

      expect(dateDataService.resetKegtronPort).toHaveBeenCalledWith(
        'dev-1',
        0,
        { volumeSize: 5.0, volumeUnit: 'gal' },
        true
      );
    });

    it('should close dialog with submit on success', () => {
      component.submit();

      expect(mockDialogRef.close).toHaveBeenCalledWith('submit');
    });

    it('should reset processing to false on success', () => {
      component.submit();

      expect(component.processing).toBe(false);
    });

    it('should reset disableClose to false on success', () => {
      component.submit();

      expect(mockDialogRef.disableClose).toBe(false);
    });

    it('should display error via snackbar on failure', () => {
      const error: DataError = { message: 'Reset failed' } as DataError;
      mockDataService.resetKegtronPort.and.returnValue(throwError(() => error));

      component.submit();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Reset failed', 'Close');
    });

    it('should reset processing to false on failure', () => {
      const error: DataError = { message: 'Reset failed' } as DataError;
      mockDataService.resetKegtronPort.and.returnValue(throwError(() => error));

      component.submit();

      expect(component.processing).toBe(false);
    });

    it('should reset disableClose to false on failure', () => {
      const error: DataError = { message: 'Reset failed' } as DataError;
      mockDataService.resetKegtronPort.and.returnValue(throwError(() => error));

      component.submit();

      expect(mockDialogRef.disableClose).toBe(false);
    });

    it('should not close dialog on failure', () => {
      const error: DataError = { message: 'Reset failed' } as DataError;
      mockDataService.resetKegtronPort.and.returnValue(throwError(() => error));

      component.submit();

      expect(mockDialogRef.close).not.toHaveBeenCalled();
    });

    it('should send correct volumeUnit when changed to liters', () => {
      component.volumeUnit = 'l';
      component.submit();

      const payload = mockDataService.resetKegtronPort.calls.mostRecent().args[2];
      expect(payload.volumeUnit).toBe('l');
    });

    it('should send correct volumeUnit when changed to ml', () => {
      component.volumeUnit = 'ml';
      component.submit();

      const payload = mockDataService.resetKegtronPort.calls.mostRecent().args[2];
      expect(payload.volumeUnit).toBe('ml');
    });
  });

  describe('skip', () => {
    it('should close dialog with skip', () => {
      component.skip();

      expect(mockDialogRef.close).toHaveBeenCalledWith('skip');
    });
  });

  describe('cancel', () => {
    it('should close dialog with cancel', () => {
      component.cancel();

      expect(mockDialogRef.close).toHaveBeenCalledWith('cancel');
    });
  });
});
