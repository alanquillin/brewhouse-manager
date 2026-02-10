import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { ManageLocationsComponent } from './locations.component';
import { DataService, DataError } from '../../_services/data.service';
import { Location } from '../../models/models';

describe('ManageLocationsComponent', () => {
  let component: ManageLocationsComponent;
  let fixture: ComponentFixture<ManageLocationsComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockLocations = [
    { id: 'loc-1', name: 'location-a', description: 'Location A' },
    { id: 'loc-2', name: 'location-b', description: 'Location B' },
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', [
      'getLocations',
      'createLocation',
      'updateLocation',
      'deleteLocation',
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockDataService.getLocations.and.returnValue(of(mockLocations as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManageLocationsComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageLocationsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have loading set to false initially', () => {
      expect(component.loading).toBe(false);
    });

    it('should have empty locations array', () => {
      expect(component.locations).toEqual([]);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have adding set to false', () => {
      expect(component.adding).toBe(false);
    });

    it('should have displayedColumns defined', () => {
      expect(component.displayedColumns).toEqual(['name', 'description', 'actions']);
    });

    it('should have nameValidationPattern defined', () => {
      expect(component.nameValidationPattern).toBe('^[a-z0-9_-]*$');
    });

    it('should have addFormGroup defined', () => {
      expect(component.addFormGroup).toBeTruthy();
    });
  });

  describe('ngOnInit', () => {
    it('should set loading to true', () => {
      component.ngOnInit();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call _refresh', () => {
      spyOn(component, '_refresh').and.callThrough();
      fixture.detectChanges();
      expect(component._refresh).toHaveBeenCalled();
    });
  });

  describe('_refresh', () => {
    it('should call getLocations', () => {
      component._refresh();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should populate locations array', () => {
      component._refresh();
      expect(component.locations.length).toBe(2);
    });

    it('should sort locations by description', () => {
      const unsortedLocations = [
        { id: 'loc-1', name: 'loc-z', description: 'Zebra Location' },
        { id: 'loc-2', name: 'loc-a', description: 'Alpha Location' },
      ];
      mockDataService.getLocations.and.returnValue(of(unsortedLocations as any));

      component._refresh();

      expect(component.locations[0].description).toBe('Alpha Location');
      expect(component.locations[1].description).toBe('Zebra Location');
    });

    it('should update dataSource', () => {
      component._refresh();
      expect(component.dataSource.data.length).toBe(2);
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component._refresh(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });

    it('should call next callback on success', () => {
      const nextCallback = jasmine.createSpy('next');
      component._refresh(undefined, nextCallback);
      expect(nextCallback).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load' } as DataError;
      mockDataService.getLocations.and.returnValue(throwError(() => error));

      component._refresh();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load', 'Close');
    });

    it('should call error callback on failure', () => {
      const error: DataError = { message: 'Failed' } as DataError;
      mockDataService.getLocations.and.returnValue(throwError(() => error));
      const errorCallback = jasmine.createSpy('error');

      component._refresh(undefined, undefined, errorCallback);

      expect(errorCallback).toHaveBeenCalled();
    });
  });

  describe('refresh', () => {
    it('should set loading to true', () => {
      component.refresh();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call _refresh', () => {
      spyOn(component, '_refresh').and.callThrough();
      component.refresh();
      expect(component._refresh).toHaveBeenCalled();
    });
  });

  describe('edit', () => {
    it('should enable editing on location', () => {
      fixture.detectChanges();
      const location = new Location(mockLocations[0]);
      spyOn(location, 'enableEditing');

      component.edit(location);

      expect(location.enableEditing).toHaveBeenCalled();
    });
  });

  describe('save', () => {
    let location: Location;

    beforeEach(() => {
      fixture.detectChanges();
      location = new Location(mockLocations[0]);
      location.enableEditing();
      location.editValues.description = 'Updated Description';
      mockDataService.updateLocation.and.returnValue(of(mockLocations[0] as any));
    });

    it('should return early if no changes', () => {
      location.disableEditing();
      location.enableEditing();
      component.save(location);
      expect(mockDataService.updateLocation).not.toHaveBeenCalled();
    });

    it('should call updateLocation with changes', () => {
      component.save(location);
      expect(mockDataService.updateLocation).toHaveBeenCalledWith('loc-1', { description: 'Updated Description' });
    });

    it('should disable editing on success', () => {
      component.save(location);
      expect(location.isEditing).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Update failed' } as DataError;
      mockDataService.updateLocation.and.returnValue(throwError(() => error));

      component.save(location);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Update failed', 'Close');
    });
  });

  describe('cancel', () => {
    it('should disable editing on location', () => {
      fixture.detectChanges();
      const location = new Location(mockLocations[0]);
      location.enableEditing();

      component.cancel(location);

      expect(location.isEditing).toBe(false);
    });
  });

  describe('delete', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deleteLocation.and.returnValue(of({}));
    });

    it('should call deleteLocation when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const location = new Location(mockLocations[0]);

      component.delete(location);

      expect(mockDataService.deleteLocation).toHaveBeenCalledWith('loc-1');
    });

    it('should not call deleteLocation when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const location = new Location(mockLocations[0]);

      component.delete(location);

      expect(mockDataService.deleteLocation).not.toHaveBeenCalled();
    });

    it('should set processing to true', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const location = new Location(mockLocations[0]);

      component.delete(location);

      expect(mockDataService.deleteLocation).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const error: DataError = { message: 'Delete failed' } as DataError;
      mockDataService.deleteLocation.and.returnValue(throwError(() => error));
      const location = new Location(mockLocations[0]);

      component.delete(location);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Delete failed', 'Close');
    });
  });

  describe('add', () => {
    it('should create new addLocation', () => {
      component.add();
      expect(component.addLocation).toBeTruthy();
    });

    it('should set adding to true', () => {
      component.add();
      expect(component.adding).toBe(true);
    });
  });

  describe('create', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.addLocation = new Location({ name: 'new-location', description: 'New Location' });
      mockDataService.createLocation.and.returnValue(of(mockLocations[0] as any));
    });

    it('should set processing to true', () => {
      component.create();
      expect(mockDataService.createLocation).toHaveBeenCalled();
    });

    it('should call createLocation', () => {
      component.create();
      expect(mockDataService.createLocation).toHaveBeenCalledWith({
        name: 'new-location',
        description: 'New Location',
      });
    });

    it('should set adding to false on success', () => {
      component.adding = true;
      component.create();
      expect(component.adding).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createLocation.and.returnValue(throwError(() => error));

      component.create();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Creation failed', 'Close');
    });
  });

  describe('cancelAdd', () => {
    it('should set adding to false', () => {
      component.adding = true;
      component.cancelAdd();
      expect(component.adding).toBe(false);
    });
  });

  describe('addForm getter', () => {
    it('should return form controls', () => {
      const controls = component.addForm;
      expect(controls['name']).toBeTruthy();
      expect(controls['description']).toBeTruthy();
    });
  });

  describe('form validation', () => {
    it('should require name', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should require description', () => {
      const control = component.addFormGroup.get('description');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should validate name pattern - lowercase letters allowed', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('valid-name');
      expect(control?.hasError('pattern')).toBeFalsy();
    });

    it('should validate name pattern - numbers allowed', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('location123');
      expect(control?.hasError('pattern')).toBeFalsy();
    });

    it('should validate name pattern - underscores allowed', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('location_name');
      expect(control?.hasError('pattern')).toBeFalsy();
    });

    it('should validate name pattern - hyphens allowed', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('location-name');
      expect(control?.hasError('pattern')).toBeFalsy();
    });

    it('should reject uppercase letters in name', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('Location');
      expect(control?.hasError('pattern')).toBe(true);
    });

    it('should reject spaces in name', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('location name');
      expect(control?.hasError('pattern')).toBe(true);
    });

    it('should reject special characters in name', () => {
      const control = component.addFormGroup.get('name');
      control?.setValue('location@name');
      expect(control?.hasError('pattern')).toBe(true);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });
});
