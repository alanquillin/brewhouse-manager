import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { ManageTapsComponent } from './taps.component';
import { CurrentUserService } from '../../_services/current-user.service';
import { DataService, DataError } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';
import { Batch, Beer, Beverage, Location, Tap, TapMonitor, UserInfo } from '../../models/models';

describe('ManageTapsComponent', () => {
  let component: ManageTapsComponent;
  let fixture: ComponentFixture<ManageTapsComponent>;
  let mockCurrentUserService: jasmine.SpyObj<CurrentUserService>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockUserInfo = {
    id: 'user-1',
    email: 'admin@example.com',
    firstName: 'Admin',
    lastName: 'User',
    admin: true,
    locations: [{ id: 'loc-1', name: 'Location 1' }],
  };

  const mockLocations = [
    { id: 'loc-1', name: 'location-1', description: 'Location 1' },
    { id: 'loc-2', name: 'location-2', description: 'Location 2' },
  ];

  const mockBeers = [
    { id: 'beer-1', name: 'IPA', description: 'India Pale Ale' },
    { id: 'beer-2', name: 'Stout', description: 'Dark Stout' },
  ];

  const mockBeverages = [
    { id: 'bev-1', name: 'Coffee', type: 'nitro-coffee' },
    { id: 'bev-2', name: 'Kombucha', type: 'kombucha' },
  ];

  const mockTapMonitors = [
    { id: 'tm-1', name: 'Monitor 1', monitorType: 'plaato-blynk', locationId: 'loc-1' },
    { id: 'tm-2', name: 'Monitor 2', monitorType: 'kegtron', locationId: 'loc-2' },
  ];

  const mockBatches = [
    { id: 'batch-1', beerId: 'beer-1', batchNumber: '1', locationIds: ['loc-1'] },
    { id: 'batch-2', beverageId: 'bev-1', batchNumber: '1', locationIds: ['loc-1'] },
  ];

  const mockTaps = [
    {
      id: 'tap-1',
      description: 'Tap 1',
      tapNumber: 1,
      locationId: 'loc-1',
      beerId: 'beer-1',
      location: mockLocations[0],
    },
    {
      id: 'tap-2',
      description: 'Tap 2',
      tapNumber: 2,
      locationId: 'loc-2',
      beverageId: 'bev-1',
      location: mockLocations[1],
    },
  ];

  beforeEach(async () => {
    mockCurrentUserService = jasmine.createSpyObj('CurrentUserService', ['getCurrentUser']);
    mockDataService = jasmine.createSpyObj('DataService', [
      'getLocations',
      'getBeers',
      'getBeverages',
      'getTapMonitors',
      'getBatches',
      'getTaps',
      'createTap',
      'updateTap',
      'deleteTap',
      'clearTap',
    ]);
    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockCurrentUserService.getCurrentUser.and.returnValue(of(mockUserInfo as any));
    mockDataService.getLocations.and.returnValue(of(mockLocations as any));
    mockDataService.getBeers.and.returnValue(of(mockBeers as any));
    mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
    mockDataService.getTapMonitors.and.returnValue(of(mockTapMonitors as any));
    mockDataService.getBatches.and.returnValue(of(mockBatches as any));
    mockDataService.getTaps.and.returnValue(of(mockTaps as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManageTapsComponent],
      providers: [
        { provide: CurrentUserService, useValue: mockCurrentUserService },
        { provide: DataService, useValue: mockDataService },
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageTapsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have empty taps array', () => {
      expect(component.taps).toEqual([]);
    });

    it('should have loading set to false', () => {
      expect(component.loading).toBe(false);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have adding set to false', () => {
      expect(component.adding).toBe(false);
    });

    it('should have editing set to false', () => {
      expect(component.editing).toBe(false);
    });

    it('should have modifyFormGroup defined', () => {
      expect(component.modifyFormGroup).toBeTruthy();
    });
  });

  describe('ngOnInit', () => {
    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on success', () => {
      fixture.detectChanges();
      expect(component.userInfo.email).toBe('admin@example.com');
    });

    it('should populate selectedLocationFilters for admin', () => {
      fixture.detectChanges();
      expect(component.selectedLocationFilters).toContain('loc-1');
    });

    it('should call _refreshAll', () => {
      fixture.detectChanges();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should display error on failure (non-401)', () => {
      const error: DataError = { message: 'Failed', statusCode: 500 } as DataError;
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed', 'Close');
    });

    it('should not display error on 401 status', () => {
      const error: DataError = { message: 'Unauthorized', statusCode: 401 } as DataError;
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).not.toHaveBeenCalled();
    });
  });

  describe('_refreshAll', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getLocations', () => {
      component._refreshAll();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call getBeers', () => {
      component._refreshAll();
      expect(mockDataService.getBeers).toHaveBeenCalled();
    });

    it('should call getTapMonitors', () => {
      component._refreshAll();
      expect(mockDataService.getTapMonitors).toHaveBeenCalled();
    });

    it('should call getBeverages', () => {
      component._refreshAll();
      expect(mockDataService.getBeverages).toHaveBeenCalled();
    });

    it('should call getBatches', () => {
      component._refreshAll();
      expect(mockDataService.getBatches).toHaveBeenCalled();
    });

    it('should populate locations', () => {
      component._refreshAll();
      expect(component.locations.length).toBe(2);
    });

    it('should populate beers', () => {
      component._refreshAll();
      expect(component.beers.length).toBe(2);
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component._refreshAll(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });
  });

  describe('refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getTaps', () => {
      component.refresh();
      expect(mockDataService.getTaps).toHaveBeenCalled();
    });

    it('should populate taps array', () => {
      component.refresh();
      expect(component.taps.length).toBe(2);
    });

    it('should call filter', () => {
      spyOn(component, 'filter');
      component.refresh();
      expect(component.filter).toHaveBeenCalled();
    });
  });

  describe('displayedColumns getter', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should include location when multiple locations exist', () => {
      component.locations = mockLocations as any;
      const columns = component.displayedColumns;
      expect(columns).toContain('location');
    });

    it('should not include location when single location exists', () => {
      component.locations = [mockLocations[0]] as any;
      const columns = component.displayedColumns;
      expect(columns).not.toContain('location');
    });

    it('should always include tapNumber', () => {
      const columns = component.displayedColumns;
      expect(columns).toContain('tapNumber');
    });

    it('should always include actions', () => {
      const columns = component.displayedColumns;
      expect(columns).toContain('actions');
    });
  });

  describe('add', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should reset modifyFormGroup', () => {
      spyOn(component.modifyFormGroup, 'reset');
      component.add();
      expect(component.modifyFormGroup.reset).toHaveBeenCalled();
    });

    it('should set adding to true', () => {
      component.add();
      expect(component.adding).toBe(true);
    });

    it('should create new modifyTap', () => {
      component.add();
      expect(component.modifyTap).toBeTruthy();
    });

    it('should set locationId when single location', () => {
      component.locations = [new Location(mockLocations[0])];
      component.add();
      expect(component.modifyTap.editValues.locationId).toBe('loc-1');
    });
  });

  describe('create', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTap = new Tap({ editValues: {} } as any);
      component.modifyTap.enableEditing();
      component.modifyTap.editValues = {
        description: 'New Tap',
        tapNumber: 3,
        locationId: 'loc-1',
        namePrefix: '',
        nameSuffix: '',
      };
      mockDataService.createTap.and.returnValue(of(mockTaps[0] as any));
    });

    it('should set processing to true', () => {
      component.create();
      expect(mockDataService.createTap).toHaveBeenCalled();
    });

    it('should call createTap', () => {
      component.create();
      expect(mockDataService.createTap).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createTap.and.returnValue(throwError(() => error));

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

  describe('edit', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should enable editing on tap', () => {
      const tap = new Tap(mockTaps[0] as any);
      component.edit(tap);
      expect(tap.isEditing).toBe(true);
    });

    it('should set modifyTap', () => {
      const tap = new Tap(mockTaps[0] as any);
      component.edit(tap);
      expect(component.modifyTap).toBe(tap);
    });

    it('should set editing to true', () => {
      const tap = new Tap(mockTaps[0] as any);
      component.edit(tap);
      expect(component.editing).toBe(true);
    });
  });

  describe('save', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTap = new Tap(mockTaps[0] as any);
      component.modifyTap.enableEditing();
      component.modifyTap.editValues.description = 'Updated Description';
      mockDataService.updateTap.and.returnValue(of(mockTaps[0] as any));
    });

    it('should set processing to true', () => {
      component.save();
      expect(mockDataService.updateTap).toHaveBeenCalled();
    });

    it('should call updateTap', () => {
      component.save();
      expect(mockDataService.updateTap).toHaveBeenCalledWith('tap-1', jasmine.any(Object));
    });

    it('should disable editing on success', () => {
      component.save();
      expect(component.modifyTap.isEditing).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Update failed' } as DataError;
      mockDataService.updateTap.and.returnValue(throwError(() => error));

      component.save();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Update failed', 'Close');
    });
  });

  describe('cancelEdit', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTap = new Tap(mockTaps[0] as any);
      component.modifyTap.enableEditing();
      component.editing = true;
    });

    it('should disable editing on modifyTap', () => {
      component.cancelEdit();
      expect(component.modifyTap.isEditing).toBe(false);
    });

    it('should set editing to false', () => {
      component.cancelEdit();
      expect(component.editing).toBe(false);
    });
  });

  describe('delete', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deleteTap.and.returnValue(of({}));
    });

    it('should call deleteTap when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const tap = new Tap(mockTaps[0] as any);

      component.delete(tap);

      expect(mockDataService.deleteTap).toHaveBeenCalledWith('tap-1');
    });

    it('should not call deleteTap when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const tap = new Tap(mockTaps[0] as any);

      component.delete(tap);

      expect(mockDataService.deleteTap).not.toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const error: DataError = { message: 'Delete failed' } as DataError;
      mockDataService.deleteTap.and.returnValue(throwError(() => error));
      const tap = new Tap(mockTaps[0] as any);

      component.delete(tap);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Delete failed', 'Close');
    });
  });

  describe('clear', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.clearTap.and.returnValue(of({}));
    });

    it('should call clearTap when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const tap = new Tap(mockTaps[0] as any);

      component.clear(tap);

      expect(mockDataService.clearTap).toHaveBeenCalledWith('tap-1');
    });

    it('should not call clearTap when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const tap = new Tap(mockTaps[0] as any);

      component.clear(tap);

      expect(mockDataService.clearTap).not.toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const error: DataError = { message: 'Clear failed' } as DataError;
      mockDataService.clearTap.and.returnValue(throwError(() => error));
      const tap = new Tap(mockTaps[0] as any);

      component.clear(tap);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Clear failed', 'Close');
    });
  });

  describe('filter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.taps = mockTaps.map(t => new Tap(t as any));
    });

    it('should populate filteredTaps', () => {
      component.filter();
      expect(component.filteredTaps.length).toBeGreaterThan(0);
    });

    it('should filter by selectedLocationFilters', () => {
      component.selectedLocationFilters = ['loc-1'];
      component.filter();
      expect(component.filteredTaps.every(t => t.locationId === 'loc-1')).toBe(true);
    });

    it('should show all when no location filters', () => {
      component.selectedLocationFilters = [];
      component.filter();
      expect(component.filteredTaps.length).toBe(2);
    });
  });

  describe('findBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.beers = mockBeers.map(b => new Beer(b as any));
    });

    it('should find beer by id', () => {
      const beer = component.findBeer('beer-1');
      expect(beer?.id).toBe('beer-1');
    });

    it('should return undefined for unknown id', () => {
      const beer = component.findBeer('unknown');
      expect(beer).toBeUndefined();
    });
  });

  describe('findBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.beverages = mockBeverages.map(b => new Beverage(b as any));
    });

    it('should find beverage by id', () => {
      const beverage = component.findBeverage('bev-1');
      expect(beverage?.id).toBe('bev-1');
    });

    it('should return undefined for unknown id', () => {
      const beverage = component.findBeverage('unknown');
      expect(beverage).toBeUndefined();
    });
  });

  describe('findBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.batches = mockBatches.map(b => new Batch(b as any));
    });

    it('should find batch by id', () => {
      const batch = component.findBatch('batch-1');
      expect(batch?.id).toBe('batch-1');
    });

    it('should return undefined for unknown id', () => {
      const batch = component.findBatch('unknown');
      expect(batch).toBeUndefined();
    });
  });

  describe('getTapMonitorsForLocation', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.tapMonitors = mockTapMonitors as any;
    });

    it('should return tap monitors for location', () => {
      const monitors = component.getTapMonitorsForLocation('loc-1');
      expect(monitors.length).toBe(1);
      expect(monitors[0].id).toBe('tm-1');
    });

    it('should return empty array for unknown location', () => {
      const monitors = component.getTapMonitorsForLocation('unknown');
      expect(monitors).toEqual([]);
    });

    it('should return empty array for undefined location', () => {
      const monitors = component.getTapMonitorsForLocation(undefined);
      expect(monitors).toEqual([]);
    });
  });

  describe('getTapMonitorName', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.tapMonitors = mockTapMonitors as any;
    });

    it('should return monitor name with type', () => {
      const monitor = mockTapMonitors[0] as TapMonitor;
      const name = component.getTapMonitorName(monitor);
      expect(name).toBe('Monitor 1 (plaato-blynk)');
    });

    it('should return empty string for undefined monitor', () => {
      const name = component.getTapMonitorName(undefined);
      expect(name).toBe('');
    });

    it('should find monitor by id if not provided directly', () => {
      const name = component.getTapMonitorName(undefined, 'tm-1');
      expect(name).toBe('Monitor 1 (plaato-blynk)');
    });

    it('should return UNNAMED for monitor with empty name', () => {
      const monitor = { id: 'tm-3', name: '', monitorType: 'test' } as TapMonitor;
      const name = component.getTapMonitorName(monitor);
      expect(name).toBe('UNNAMED (test)');
    });
  });

  describe('modifyForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyForm;
      expect(controls['description']).toBeTruthy();
      expect(controls['tapNumber']).toBeTruthy();
      expect(controls['locationId']).toBeTruthy();
    });
  });

  describe('showDisplayNameToolTip', () => {
    it('should return true when namePrefix is set', () => {
      const tap = new Tap({ namePrefix: 'Draft: ' } as any);
      expect(component.showDisplayNameToolTip(tap)).toBe(true);
    });

    it('should return true when nameSuffix is set', () => {
      const tap = new Tap({ nameSuffix: ' (Limited)' } as any);
      expect(component.showDisplayNameToolTip(tap)).toBe(true);
    });

    it('should return false when neither is set', () => {
      const tap = new Tap({} as any);
      expect(component.showDisplayNameToolTip(tap)).toBe(false);
    });
  });

  describe('getBeerBatches', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.batches = mockBatches.map(b => new Batch(b as any));
      component.beers = mockBeers.map(b => new Beer(b as any));
      // Set up beer reference
      component.batches[0].beer = component.beers[0];
    });

    it('should return beer batches for location', () => {
      const batches = component.getBeerBatches('loc-1');
      expect(batches.length).toBe(1);
    });

    it('should return empty array for location with no beer batches', () => {
      const batches = component.getBeerBatches('loc-2');
      expect(batches).toEqual([]);
    });
  });

  describe('getBeverageBatches', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.batches = mockBatches.map(b => new Batch(b as any));
      component.beverages = mockBeverages.map(b => new Beverage(b as any));
      // Set up beverage reference
      component.batches[1].beverage = component.beverages[0];
    });

    it('should return beverage batches for location', () => {
      const batches = component.getBeverageBatches('loc-1');
      expect(batches.length).toBe(1);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });
});
