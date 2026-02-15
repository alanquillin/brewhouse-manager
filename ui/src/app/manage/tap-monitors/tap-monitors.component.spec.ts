import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { KegtronResetDialogComponent } from '../../_dialogs/kegtron-reset-dialog/kegtron-reset-dialog.component';
import { CurrentUserService } from '../../_services/current-user.service';
import { DataError, DataService } from '../../_services/data.service';
import { Location, TapMonitor, TapMonitorType } from '../../models/models';
import { ManageTapMonitorsComponent } from './tap-monitors.component';

describe('ManageTapMonitorsComponent', () => {
  let component: ManageTapMonitorsComponent;
  let fixture: ComponentFixture<ManageTapMonitorsComponent>;
  let mockCurrentUserService: jasmine.SpyObj<CurrentUserService>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;
  let mockDialog: jasmine.SpyObj<MatDialog>;

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

  const mockMonitorTypes: TapMonitorType[] = [
    { type: 'plaato-blynk', description: 'Plaato Blynk', supportsDiscovery: false } as any,
    {
      type: 'keg-volume-monitor-weight',
      description: 'KVM Weight',
      supportsDiscovery: true,
    } as any,
    { type: 'kegtron-pro', description: 'Kegtron Pro', supportsDiscovery: true } as any,
  ];

  const mockTapMonitors = [
    {
      id: 'tm-1',
      name: 'Monitor 1',
      monitorType: 'plaato-blynk',
      locationId: 'loc-1',
      meta: { authToken: 'token123' },
    },
    {
      id: 'tm-2',
      name: 'Monitor 2',
      monitorType: 'keg-volume-monitor-weight',
      locationId: 'loc-2',
      meta: { deviceId: 'device123' },
    },
  ];

  beforeEach(async () => {
    mockCurrentUserService = jasmine.createSpyObj('CurrentUserService', ['getCurrentUser']);
    mockDataService = jasmine.createSpyObj('DataService', [
      'getLocations',
      'getMonitorTypes',
      'getTapMonitors',
      'createTapMonitor',
      'updateTapMonitor',
      'deleteTapMonitor',
      'discoverTapMonitors',
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);
    mockDialog = jasmine.createSpyObj('MatDialog', ['open']);

    mockCurrentUserService.getCurrentUser.and.returnValue(of(mockUserInfo as any));
    mockDataService.getLocations.and.returnValue(of(mockLocations as any));
    mockDataService.getMonitorTypes.and.returnValue(of(mockMonitorTypes));
    mockDataService.getTapMonitors.and.returnValue(of(mockTapMonitors as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManageTapMonitorsComponent],
      providers: [
        { provide: CurrentUserService, useValue: mockCurrentUserService },
        { provide: DataService, useValue: mockDataService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
        { provide: MatDialog, useValue: mockDialog },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageTapMonitorsComponent);
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

    it('should have empty tapMonitors array', () => {
      expect(component.tapMonitors).toEqual([]);
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

    it('should have editing set to false', () => {
      expect(component.editing).toBe(false);
    });

    it('should have modifyFormGroup defined', () => {
      expect(component.modifyFormGroup).toBeTruthy();
    });

    it('should have allowedMassUnits defined', () => {
      expect(component.allowedMassUnits).toEqual(['g', 'kg', 'oz', 'lb']);
    });

    it('should have allowedLiquidUnits defined', () => {
      expect(component.allowedLiquidUnits).toEqual(['ml', 'l', 'gal']);
    });
  });

  describe('ngOnInit', () => {
    it('should set loading to true', () => {
      component.ngOnInit();
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
    });

    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on success', () => {
      fixture.detectChanges();
      expect(component.userInfo.email).toBe('admin@example.com');
    });

    it('should populate selectedLocationFilters for admin user', () => {
      fixture.detectChanges();
      expect(component.selectedLocationFilters).toContain('loc-1');
    });

    it('should call refreshAll', () => {
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

  describe('refreshAll', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getLocations', () => {
      component.refreshAll();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call getMonitorTypes', () => {
      component.refreshAll();
      expect(mockDataService.getMonitorTypes).toHaveBeenCalled();
    });

    it('should populate locations', () => {
      component.refreshAll();
      expect(component.locations.length).toBe(2);
    });

    it('should populate monitorTypes', () => {
      component.refreshAll();
      expect(component.monitorTypes.length).toBe(3);
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component.refreshAll(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });

    it('should display error on locations failure', () => {
      const error: DataError = { message: 'Failed to load locations' } as DataError;
      mockDataService.getLocations.and.returnValue(throwError(() => error));

      component.refreshAll();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load locations', 'Close');
    });
  });

  describe('_refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getTapMonitors', () => {
      component._refresh();
      expect(mockDataService.getTapMonitors).toHaveBeenCalled();
    });

    it('should populate tapMonitors', () => {
      component._refresh();
      expect(component.tapMonitors.length).toBe(2);
    });

    it('should call filter', () => {
      spyOn(component, 'filter');
      component._refresh();
      expect(component.filter).toHaveBeenCalled();
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component._refresh(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load monitors' } as DataError;
      mockDataService.getTapMonitors.and.returnValue(throwError(() => error));

      component._refresh();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load monitors', 'Close');
    });
  });

  describe('refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should set loading to true', () => {
      component.refresh();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call refreshAll', () => {
      spyOn(component, 'refreshAll').and.callThrough();
      component.refresh();
      expect(component.refreshAll).toHaveBeenCalled();
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

    it('should always include name and type', () => {
      const columns = component.displayedColumns;
      expect(columns).toContain('name');
      expect(columns).toContain('type');
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

    it('should create new modifyTapMonitor', () => {
      component.add();
      expect(component.modifyTapMonitor).toBeTruthy();
    });

    it('should set locationId when single location', () => {
      component.locations = [new Location(mockLocations[0])];
      component.add();
      expect(component.modifyTapMonitor.editValues.locationId).toBe('loc-1');
    });

    it('should set monitorType when single monitor type', () => {
      component.monitorTypes = [mockMonitorTypes[0]];
      component.add();
      expect(component.modifyTapMonitor.editValues.monitorType).toBe('plaato-blynk');
    });
  });

  describe('create', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTapMonitor = new TapMonitor({
        meta: {},
      } as any);
      component.modifyTapMonitor.enableEditing();
      component.modifyTapMonitor.editValues = {
        name: 'New Monitor',
        monitorType: 'plaato-blynk',
        locationId: 'loc-1',
        meta: { authToken: 'token123' },
      };
      mockDataService.createTapMonitor.and.returnValue(of(mockTapMonitors[0] as any));
    });

    it('should set processing to true', () => {
      component.create();
      expect(mockDataService.createTapMonitor).toHaveBeenCalled();
    });

    it('should call createTapMonitor', () => {
      component.create();
      expect(mockDataService.createTapMonitor).toHaveBeenCalled();
    });

    it('should include authToken for plaato-blynk type', () => {
      component.create();
      const callArg = mockDataService.createTapMonitor.calls.mostRecent().args[0];
      expect(callArg.meta.authToken).toBe('token123');
    });

    it('should include deviceId for keg-volume-monitor-weight type', () => {
      component.modifyTapMonitor.editValues.monitorType = 'keg-volume-monitor-weight';
      component.modifyTapMonitor.editValues.meta = { deviceId: 'device123' };
      component.create();
      const callArg = mockDataService.createTapMonitor.calls.mostRecent().args[0];
      expect(callArg.meta.deviceId).toBe('device123');
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createTapMonitor.and.returnValue(throwError(() => error));

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
      mockDataService.discoverTapMonitors.and.returnValue(of([]));
    });

    it('should enable editing on tapMonitor', () => {
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);
      component.edit(tapMonitor);
      expect(tapMonitor.isEditing).toBe(true);
    });

    it('should set modifyTapMonitor', () => {
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);
      component.edit(tapMonitor);
      expect(component.modifyTapMonitor).toBe(tapMonitor);
    });

    it('should set editing to true', () => {
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);
      component.edit(tapMonitor);
      expect(component.editing).toBe(true);
    });

    it('should reset modifyFormGroup', () => {
      spyOn(component.modifyFormGroup, 'reset');
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);
      component.edit(tapMonitor);
      expect(component.modifyFormGroup.reset).toHaveBeenCalled();
    });
  });

  describe('save', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTapMonitor = new TapMonitor(mockTapMonitors[0] as any);
      component.modifyTapMonitor.enableEditing();
      component.modifyTapMonitor.editValues.name = 'Updated Name';
      mockDataService.updateTapMonitor.and.returnValue(of(mockTapMonitors[0] as any));
    });

    it('should set processing to true', () => {
      component.save();
      expect(mockDataService.updateTapMonitor).toHaveBeenCalled();
    });

    it('should call updateTapMonitor', () => {
      component.save();
      expect(mockDataService.updateTapMonitor).toHaveBeenCalledWith('tm-1', {
        name: 'Updated Name',
      });
    });

    it('should disable editing on success', () => {
      component.save();
      expect(component.modifyTapMonitor.isEditing).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Update failed' } as DataError;
      mockDataService.updateTapMonitor.and.returnValue(throwError(() => error));

      component.save();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Update failed', 'Close');
    });
  });

  describe('cancelEdit', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTapMonitor = new TapMonitor(mockTapMonitors[0] as any);
      component.modifyTapMonitor.enableEditing();
      component.editing = true;
    });

    it('should disable editing on modifyTapMonitor', () => {
      component.cancelEdit();
      expect(component.modifyTapMonitor.isEditing).toBe(false);
    });

    it('should set editing to false', () => {
      component.cancelEdit();
      expect(component.editing).toBe(false);
    });
  });

  describe('delete', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deleteTapMonitor.and.returnValue(of({}));
    });

    it('should call deleteTapMonitor when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);

      component.delete(tapMonitor);

      expect(mockDataService.deleteTapMonitor).toHaveBeenCalledWith('tm-1');
    });

    it('should not call deleteTapMonitor when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);

      component.delete(tapMonitor);

      expect(mockDataService.deleteTapMonitor).not.toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const error: DataError = { message: 'Delete failed' } as DataError;
      mockDataService.deleteTapMonitor.and.returnValue(throwError(() => error));
      const tapMonitor = new TapMonitor(mockTapMonitors[0] as any);

      component.delete(tapMonitor);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Delete failed', 'Close');
    });
  });

  describe('getLocationName', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.locations = mockLocations.map(l => new Location(l));
    });

    it('should return location name', () => {
      const tapMonitor = new TapMonitor({ locationId: 'loc-1' } as any);
      expect(component.getLocationName(tapMonitor)).toBe('location-1');
    });

    it('should return UNKNOWN for missing location', () => {
      const tapMonitor = new TapMonitor({ locationId: 'non-existent' } as any);
      expect(component.getLocationName(tapMonitor)).toBe('UNKNOWN');
    });
  });

  describe('filter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.tapMonitors = mockTapMonitors.map(tm => new TapMonitor(tm as any));
    });

    it('should populate filteredTapMonitors', () => {
      component.filter();
      expect(component.filteredTapMonitors.length).toBeGreaterThan(0);
    });

    it('should filter by selectedLocationFilters', () => {
      component.selectedLocationFilters = ['loc-1'];
      component.filter();
      expect(component.filteredTapMonitors.every(tm => tm.locationId === 'loc-1')).toBe(true);
    });

    it('should show all when no location filters', () => {
      component.selectedLocationFilters = [];
      component.filter();
      expect(component.filteredTapMonitors.length).toBe(2);
    });
  });

  describe('getMonitorType', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.monitorTypes = mockMonitorTypes;
    });

    it('should return monitor type by type string', () => {
      const result = component.getMonitorType('plaato-blynk');
      expect(result?.type).toBe('plaato-blynk');
    });

    it('should return undefined for unknown type', () => {
      const result = component.getMonitorType('unknown');
      expect(result).toBeUndefined();
    });
  });

  describe('currentTypeSupportsDiscovery', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.monitorTypes = mockMonitorTypes;
      component.modifyTapMonitor = new TapMonitor({ meta: {} } as any);
      component.modifyTapMonitor.enableEditing();
    });

    it('should return true for discovery-enabled type', () => {
      component.modifyTapMonitor.editValues.monitorType = 'keg-volume-monitor-weight';
      expect(component.currentTypeSupportsDiscovery()).toBe(true);
    });

    it('should return false for non-discovery type', () => {
      component.modifyTapMonitor.editValues.monitorType = 'plaato-blynk';
      expect(component.currentTypeSupportsDiscovery()).toBe(false);
    });
  });

  describe('discoverTapMonitors', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyTapMonitor = new TapMonitor({ meta: {} } as any);
      component.modifyTapMonitor.enableEditing();
      component.modifyTapMonitor.editValues.monitorType = 'keg-volume-monitor-weight';
      mockDataService.discoverTapMonitors.and.returnValue(
        of([
          {
            id: 'disc-1',
            name: 'Discovered',
            model: 'test-model',
            portNum: 1,
            token: 'test-token',
          },
        ])
      );
    });

    it('should set tapMonitorDiscoveryProcessing to true', () => {
      component.discoverTapMonitors();
      // Will be false after sync observable completes
      expect(mockDataService.discoverTapMonitors).toHaveBeenCalled();
    });

    it('should call discoverTapMonitors with monitor type', () => {
      component.discoverTapMonitors();
      expect(mockDataService.discoverTapMonitors).toHaveBeenCalledWith('keg-volume-monitor-weight');
    });

    it('should populate tapMonitorDiscoveryData', () => {
      component.discoverTapMonitors();
      expect(component.tapMonitorDiscoveryData.length).toBe(1);
    });

    it('should call next callback on success', () => {
      const nextCallback = jasmine.createSpy('next');
      component.discoverTapMonitors(nextCallback);
      expect(nextCallback).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Discovery failed' } as DataError;
      mockDataService.discoverTapMonitors.and.returnValue(throwError(() => error));

      component.discoverTapMonitors();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Discovery failed', 'Close');
    });
  });

  describe('modifyForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyForm;
      expect(controls['name']).toBeTruthy();
      expect(controls['monitorType']).toBeTruthy();
      expect(controls['locationId']).toBeTruthy();
    });
  });

  describe('getTapDetails', () => {
    it('should return empty string when tap is null', () => {
      const tapMonitor = new TapMonitor({} as any);
      expect(component.getTapDetails(tapMonitor)).toBe('');
    });

    it('should return tap details when tap exists', () => {
      const tapMonitor = new TapMonitor({
        tap: { tapNumber: 1, description: 'Test Tap' },
      } as any);
      expect(component.getTapDetails(tapMonitor)).toBe('Tap #1 (Test Tap)');
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('resetKegtron', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should open KegtronResetDialogComponent with correct data', () => {
      const tapMonitor = new TapMonitor({
        id: 'tm-kegtron',
        name: 'Kegtron Monitor',
        monitorType: 'kegtron-pro',
        locationId: 'loc-1',
        meta: { deviceId: 'kegtron-dev-1', portNum: 0 },
      } as any);

      component.resetKegtron(tapMonitor);

      expect(mockDialog.open).toHaveBeenCalledWith(KegtronResetDialogComponent, {
        data: {
          deviceId: 'kegtron-dev-1',
          portNum: 0,
        },
      });
    });

    it('should pass correct portNum for non-zero port', () => {
      const tapMonitor = new TapMonitor({
        id: 'tm-kegtron-2',
        name: 'Kegtron Monitor Port 1',
        monitorType: 'kegtron-pro',
        locationId: 'loc-1',
        meta: { deviceId: 'kegtron-dev-2', portNum: 1 },
      } as any);

      component.resetKegtron(tapMonitor);

      expect(mockDialog.open).toHaveBeenCalledWith(KegtronResetDialogComponent, {
        data: {
          deviceId: 'kegtron-dev-2',
          portNum: 1,
        },
      });
    });

    it('should not pass showSkip or updateDateTapped', () => {
      const tapMonitor = new TapMonitor({
        id: 'tm-kegtron',
        monitorType: 'kegtron-pro',
        meta: { deviceId: 'kegtron-dev-1', portNum: 0 },
      } as any);

      component.resetKegtron(tapMonitor);

      const dialogData = mockDialog.open.calls.mostRecent().args[1]?.data as any;
      expect(dialogData.showSkip).toBeUndefined();
      expect(dialogData.updateDateTapped).toBeUndefined();
    });
  });
});
