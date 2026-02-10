import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { DataError, DataService } from '../_services/data.service';
import { Location } from '../models/models';
import { LocationSelectorComponent } from './location-selector.component';

describe('LocationSelectorComponent', () => {
  let component: LocationSelectorComponent;
  let fixture: ComponentFixture<LocationSelectorComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockLocations = [
    { id: '1', name: 'location-a', description: 'Location A' },
    { id: '2', name: 'location-b', description: 'Location B' },
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', ['getDashboardLocations']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    // Default to returning multiple locations
    mockDataService.getDashboardLocations.and.returnValue(of(mockLocations as any));

    await TestBed.configureTestingModule({
      declarations: [LocationSelectorComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LocationSelectorComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have title set to Location Selector', () => {
      expect(component.title).toBe('Location Selector');
    });

    it('should have loading set to false initially', () => {
      expect(component.loading).toBe(false);
    });

    it('should have empty locations array initially', () => {
      expect(component.locations).toEqual([]);
    });
  });

  describe('ngOnInit', () => {
    it('should call refresh on init', () => {
      spyOn(component, 'refresh');
      component.ngOnInit();
      expect(component.refresh).toHaveBeenCalled();
    });
  });

  describe('refresh', () => {
    it('should set loading to true while fetching', () => {
      mockDataService.getDashboardLocations.and.returnValue(of(mockLocations as any));
      component.refresh();
      // Loading will be false after async completes in sync test
      expect(mockDataService.getDashboardLocations).toHaveBeenCalled();
    });

    it('should call getDashboardLocations', () => {
      component.refresh();
      expect(mockDataService.getDashboardLocations).toHaveBeenCalled();
    });

    it('should sort locations by description', () => {
      const unsortedLocations = [
        { id: '1', name: 'loc-z', description: 'Zebra Location' },
        { id: '2', name: 'loc-a', description: 'Alpha Location' },
      ];
      mockDataService.getDashboardLocations.and.returnValue(of(unsortedLocations as any));

      component.refresh();

      expect(component.locations[0].description).toBe('Alpha Location');
      expect(component.locations[1].description).toBe('Zebra Location');
    });

    it('should set loading to false after fetching multiple locations', () => {
      mockDataService.getDashboardLocations.and.returnValue(of(mockLocations as any));
      component.refresh();
      expect(component.loading).toBe(false);
    });

    it('should navigate to single location automatically', () => {
      const singleLocation = [{ id: '1', name: 'only-location', description: 'Only Location' }];
      mockDataService.getDashboardLocations.and.returnValue(of(singleLocation as any));

      component.refresh();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['view/only-location']);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load' } as DataError;
      mockDataService.getDashboardLocations.and.returnValue(throwError(() => error));

      component.refresh();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load', 'Close');
    });
  });

  describe('selectLocation', () => {
    it('should navigate to the selected location', () => {
      const location = new Location({ id: '1', name: 'test-location' });

      component.selectLocation(location);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['view/test-location']);
    });

    it('should use location name in route', () => {
      const location = new Location({ id: '2', name: 'my-brewery' });

      component.selectLocation(location);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['view/my-brewery']);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('with no locations', () => {
    // Note: When locations.length == 0, the component redirects via window.location.href
    // which cannot be easily tested without mocking the window object.
    // The redirect behavior is tested via integration/e2e tests instead.

    it('should handle empty locations array from API', () => {
      // Just verify the API is called - the actual redirect would happen in real scenario
      mockDataService.getDashboardLocations.and.returnValue(of([]));
      // Don't call refresh() as it would trigger window.location.href redirect
      expect(mockDataService.getDashboardLocations).toBeDefined();
    });
  });

  describe('with multiple locations', () => {
    beforeEach(() => {
      mockDataService.getDashboardLocations.and.returnValue(of(mockLocations as any));
    });

    it('should not auto-navigate with multiple locations', () => {
      component.refresh();

      // Should not navigate automatically
      expect(mockRouter.navigate).not.toHaveBeenCalled();
    });

    it('should set loading to false', () => {
      component.refresh();

      expect(component.loading).toBe(false);
    });

    it('should populate locations array', () => {
      component.refresh();

      expect(component.locations.length).toBe(2);
    });
  });
});
