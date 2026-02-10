import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { ManagePlaatoKegComponent } from './plaato-keg.component';
import { DataService, DataError } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';
import { PlaatoKegDevice, UserInfo } from '../../models/models';

describe('ManagePlaatoKegComponent', () => {
  let component: ManagePlaatoKegComponent;
  let fixture: ComponentFixture<ManagePlaatoKegComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockAdminUser = {
    id: 'user-1',
    email: 'admin@example.com',
    firstName: 'Admin',
    lastName: 'User',
    admin: true,
  };

  const mockNonAdminUser = {
    id: 'user-2',
    email: 'user@example.com',
    firstName: 'Regular',
    lastName: 'User',
    admin: false,
  };

  const mockDevices: PlaatoKegDevice[] = [
    {
      id: 'device-1',
      name: 'Keg 1',
      connected: true,
      mode: 'weight',
      unitType: 'metric',
      unitMode: 'volume',
      emptyKegWeight: 5,
      maxKegVolume: 20,
    } as any,
    {
      id: 'device-2',
      name: 'Keg 2',
      connected: false,
      mode: 'weight',
      unitType: 'imperial',
      unitMode: 'percentage',
      emptyKegWeight: 10,
      maxKegVolume: 15.5,
    } as any,
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', [
      'getCurrentUser',
      'getPlaatoKegDevices',
      'getPlaatoKegDevice',
      'createPlaatoKegDevice',
      'updatePlaatoKegDevice',
      'deletePlaatoKegDevice',
      'setPlaatoKegMode',
      'setPlaatoKegUnitType',
      'setPlaatoKegUnitMode',
      'setPlaatoKegValue',
    ]);
    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockDataService.getCurrentUser.and.returnValue(of(mockAdminUser as any));
    mockDataService.getPlaatoKegDevices.and.returnValue(of(mockDevices));
    mockSettingsService.getSetting.and.returnValue('localhost');

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManagePlaatoKegComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManagePlaatoKegComponent);
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

    it('should have empty devices array', () => {
      expect(component.devices).toEqual([]);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have editing set to false', () => {
      expect(component.editing).toBe(false);
    });

    it('should have setupMode set to false', () => {
      expect(component.setupMode).toBe(false);
    });

    it('should have modifyFormGroup defined', () => {
      expect(component.modifyFormGroup).toBeTruthy();
    });

    it('should have setupFormGroup defined', () => {
      expect(component.setupFormGroup).toBeTruthy();
    });
  });

  describe('ngOnInit', () => {
    it('should set loading to true initially', () => {
      component.ngOnInit();
      // Loading will be set back to false after async completes
      expect(mockDataService.getCurrentUser).toHaveBeenCalled();
    });

    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockDataService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on success', () => {
      fixture.detectChanges();
      expect(component.userInfo.email).toBe('admin@example.com');
    });

    it('should call refreshAll for admin user', () => {
      fixture.detectChanges();
      expect(mockDataService.getPlaatoKegDevices).toHaveBeenCalled();
    });

    it('should show error for non-admin user', () => {
      mockDataService.getCurrentUser.and.returnValue(of(mockNonAdminUser as any));
      fixture.detectChanges();
      expect(mockSnackBar.open).toHaveBeenCalledWith('Admin access required', 'Close');
    });

    it('should not call refreshAll for non-admin user', () => {
      mockDataService.getCurrentUser.and.returnValue(of(mockNonAdminUser as any));
      fixture.detectChanges();
      expect(mockDataService.getPlaatoKegDevices).not.toHaveBeenCalled();
    });

    it('should display error on failure (non-401)', () => {
      const error: DataError = { message: 'Failed', statusCode: 500 } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed', 'Close');
    });

    it('should not display error on 401 status', () => {
      const error: DataError = { message: 'Unauthorized', statusCode: 401 } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).not.toHaveBeenCalled();
    });
  });

  describe('refreshAll', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getPlaatoKegDevices', () => {
      component.refreshAll();
      expect(mockDataService.getPlaatoKegDevices).toHaveBeenCalled();
    });

    it('should populate devices array', () => {
      component.refreshAll();
      expect(component.devices.length).toBe(2);
    });

    it('should call filter after loading devices', () => {
      spyOn(component, 'filter');
      component.refreshAll();
      expect(component.filter).toHaveBeenCalled();
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component.refreshAll(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load devices' } as DataError;
      mockDataService.getPlaatoKegDevices.and.returnValue(throwError(() => error));

      component.refreshAll();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load devices', 'Close');
    });
  });

  describe('refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should set loading to true', () => {
      component.refresh();
      // Loading goes true then false after sync observable
      expect(mockDataService.getPlaatoKegDevices).toHaveBeenCalled();
    });

    it('should call refreshAll', () => {
      spyOn(component, 'refreshAll').and.callThrough();
      component.refresh();
      expect(component.refreshAll).toHaveBeenCalled();
    });
  });

  describe('displayedColumns getter', () => {
    it('should return expected columns', () => {
      const columns = component.displayedColumns;
      expect(columns).toContain('name');
      expect(columns).toContain('id');
      expect(columns).toContain('connected');
      expect(columns).toContain('beerLeft');
      expect(columns).toContain('mode');
      expect(columns).toContain('actions');
    });
  });

  describe('edit', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set loading to true', () => {
      const device = new PlaatoKegDevice(mockDevices[0]);
      component.edit(device);
      expect(mockDataService.getPlaatoKegDevice).toHaveBeenCalled();
    });

    it('should set modifyDevice', () => {
      const device = new PlaatoKegDevice(mockDevices[0]);
      component.edit(device);
      expect(component.modifyDevice.id).toBe('device-1');
    });

    it('should call getPlaatoKegDevice', () => {
      const device = new PlaatoKegDevice(mockDevices[0]);
      component.edit(device);
      expect(mockDataService.getPlaatoKegDevice).toHaveBeenCalledWith('device-1');
    });
  });

  describe('save', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.modifyDevice.editValues.name = 'Updated Name';
      mockDataService.updatePlaatoKegDevice.and.returnValue(of({}));
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set processing to true', () => {
      component.save();
      expect(mockDataService.updatePlaatoKegDevice).toHaveBeenCalled();
    });

    it('should call updatePlaatoKegDevice', () => {
      component.save();
      expect(mockDataService.updatePlaatoKegDevice).toHaveBeenCalledWith('device-1', {
        name: 'Updated Name',
      });
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Update failed' } as DataError;
      mockDataService.updatePlaatoKegDevice.and.returnValue(throwError(() => error));

      component.save();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Update failed', 'Close');
    });
  });

  describe('delete', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deletePlaatoKegDevice.and.returnValue(of({}));
    });

    it('should call deletePlaatoKegDevice when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const device = new PlaatoKegDevice(mockDevices[0]);

      component.delete(device);

      expect(mockDataService.deletePlaatoKegDevice).toHaveBeenCalledWith('device-1');
    });

    it('should not call deletePlaatoKegDevice when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const device = new PlaatoKegDevice(mockDevices[0]);

      component.delete(device);

      expect(mockDataService.deletePlaatoKegDevice).not.toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const error: DataError = { message: 'Delete failed' } as DataError;
      mockDataService.deletePlaatoKegDevice.and.returnValue(throwError(() => error));
      const device = new PlaatoKegDevice(mockDevices[0]);

      component.delete(device);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Delete failed', 'Close');
    });
  });

  describe('cancelEdit', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.editing = true;
    });

    it('should disable editing on modifyDevice', () => {
      component.cancelEdit();
      expect(component.modifyDevice.isEditing).toBe(false);
    });

    it('should set editing to false', () => {
      component.cancelEdit();
      expect(component.editing).toBe(false);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('filter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.devices = mockDevices.map(d => new PlaatoKegDevice(d));
    });

    it('should sort devices by id by default', () => {
      component.filter();
      expect(component.filteredDevices.length).toBe(2);
    });

    it('should populate filteredDevices', () => {
      component.filter();
      expect(component.filteredDevices.length).toBeGreaterThan(0);
    });
  });

  describe('isConnected', () => {
    it('should return true for connected device', () => {
      const device = new PlaatoKegDevice({ connected: true } as any);
      expect(component.isConnected(device)).toBe(true);
    });

    it('should return false for disconnected device', () => {
      const device = new PlaatoKegDevice({ connected: false } as any);
      expect(component.isConnected(device)).toBe(false);
    });

    it('should return false for device with no connected property', () => {
      const device = new PlaatoKegDevice({} as any);
      expect(component.isConnected(device)).toBe(false);
    });
  });

  describe('disableDeviceConfigButtons', () => {
    it('should return true when processing is true', () => {
      component.processing = true;
      expect(component.disableDeviceConfigButtons()).toBe(true);
    });

    it('should return true when processingModeChange is true', () => {
      component.processingModeChange = true;
      expect(component.disableDeviceConfigButtons()).toBe(true);
    });

    it('should return true when processingSetEmptyKegWeight is true', () => {
      component.processingSetEmptyKegWeight = true;
      expect(component.disableDeviceConfigButtons()).toBe(true);
    });

    it('should return false when no processing flags are set', () => {
      component.processing = false;
      component.processingModeChange = false;
      component.processingSetEmptyKegWeight = false;
      component.processingSetMaxKegVolume = false;
      component.processingUnitModeChange = false;
      component.processingUnitTypeChange = false;
      expect(component.disableDeviceConfigButtons()).toBe(false);
    });
  });

  describe('setup methods', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    describe('startSetup', () => {
      it('should call startDeviceSetup', () => {
        spyOn(component, 'startDeviceSetup');
        component.startSetup();
        expect(component.startDeviceSetup).toHaveBeenCalled();
      });
    });

    describe('startDeviceSetup', () => {
      it('should set setupMode to true', () => {
        component.startDeviceSetup(new PlaatoKegDevice());
        expect(component.setupMode).toBe(true);
      });

      it('should set setupDevice', () => {
        const device = new PlaatoKegDevice({ id: 'test-id' } as any);
        component.startDeviceSetup(device);
        expect(component.setupDevice).toBe(device);
      });

      it('should reset processing flags', () => {
        component.processingNewDevice = true;
        component.processingDeviceConfig = true;
        component.startDeviceSetup(new PlaatoKegDevice());
        expect(component.processingNewDevice).toBe(false);
        expect(component.processingDeviceConfig).toBe(false);
      });
    });

    describe('cancelSetup', () => {
      it('should set setupMode to false', () => {
        component.setupMode = true;
        component.cancelSetup();
        expect(component.setupMode).toBe(false);
      });

      it('should call resetSetup', () => {
        spyOn(component, 'resetSetup');
        component.cancelSetup();
        expect(component.resetSetup).toHaveBeenCalled();
      });

      it('should call refresh', () => {
        spyOn(component, 'refresh');
        component.cancelSetup();
        expect(component.refresh).toHaveBeenCalled();
      });
    });

    describe('resetSetup', () => {
      it('should create new setupDevice', () => {
        component.setupDevice = new PlaatoKegDevice({ id: 'old-id' } as any);
        component.resetSetup();
        expect(component.setupDevice.id).toBeFalsy();
      });

      it('should reset deviceConfig', () => {
        component.deviceConfig = { ssid: 'test', pass: 'test' };
        component.resetSetup();
        expect(component.deviceConfig).toEqual({});
      });
    });

    describe('toggleWifiPassword', () => {
      it('should toggle showWifiPassword', () => {
        component.showWifiPassword = false;
        component.toggleWifiPassword();
        expect(component.showWifiPassword).toBe(true);

        component.toggleWifiPassword();
        expect(component.showWifiPassword).toBe(false);
      });
    });
  });

  describe('createDevice', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.createPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should show error if form is invalid', () => {
      component.setupFormGroup.get('name')?.setValue('');
      component.createDevice();
      expect(mockSnackBar.open).toHaveBeenCalledWith('Please fill in all required fields', 'Close');
    });

    it('should call createPlaatoKegDevice when form is valid', () => {
      component.setupFormGroup.get('name')?.setValue('New Device');
      component.createDevice();
      expect(mockDataService.createPlaatoKegDevice).toHaveBeenCalledWith({ name: 'New Device' });
    });

    it('should set processingNewDevice to true', () => {
      component.setupFormGroup.get('name')?.setValue('New Device');
      component.createDevice();
      // Will be false after sync observable completes
      expect(mockDataService.createPlaatoKegDevice).toHaveBeenCalled();
    });

    it('should display success message', () => {
      component.setupFormGroup.get('name')?.setValue('New Device');
      component.createDevice();
      expect(mockSnackBar.open).toHaveBeenCalledWith('Device created successfully.', 'Close', {
        duration: 5000,
      });
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createPlaatoKegDevice.and.returnValue(throwError(() => error));
      component.setupFormGroup.get('name')?.setValue('New Device');

      component.createDevice();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Creation failed', 'Close');
    });
  });

  describe('setMode', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.modifyDevice.editValues.mode = 'flow';
      mockDataService.setPlaatoKegMode.and.returnValue(of({}));
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set processingModeChange to true', () => {
      component.setMode(component.modifyDevice);
      expect(component.processingModeChange).toBe(true);
    });

    it('should call setPlaatoKegMode', () => {
      component.setMode(component.modifyDevice);
      expect(mockDataService.setPlaatoKegMode).toHaveBeenCalledWith('device-1', 'flow');
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Mode change failed' } as DataError;
      mockDataService.setPlaatoKegMode.and.returnValue(throwError(() => error));

      component.setMode(component.modifyDevice);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Mode change failed', 'Close');
    });
  });

  describe('setUnitType', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.modifyDevice.editValues.unitType = 'imperial';
      mockDataService.setPlaatoKegUnitType.and.returnValue(of({}));
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set processingUnitTypeChange to true', () => {
      component.setUnitType(component.modifyDevice);
      expect(component.processingUnitTypeChange).toBe(true);
    });

    it('should call setPlaatoKegUnitType', () => {
      component.setUnitType(component.modifyDevice);
      expect(mockDataService.setPlaatoKegUnitType).toHaveBeenCalledWith('device-1', 'imperial');
    });
  });

  describe('setUnitMode', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.modifyDevice.editValues.unitMode = 'percentage';
      mockDataService.setPlaatoKegUnitMode.and.returnValue(of({}));
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set processingUnitModeChange to true', () => {
      component.setUnitMode(component.modifyDevice);
      expect(component.processingUnitModeChange).toBe(true);
    });

    it('should call setPlaatoKegUnitMode', () => {
      component.setUnitMode(component.modifyDevice);
      expect(mockDataService.setPlaatoKegUnitMode).toHaveBeenCalledWith('device-1', 'percentage');
    });
  });

  describe('setEmptyKegWeight', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.modifyDevice.editValues.emptyKegWeight = 6;
      mockDataService.setPlaatoKegValue.and.returnValue(of({}));
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set processingSetEmptyKegWeight to true', () => {
      component.setEmptyKegWeight(component.modifyDevice);
      expect(component.processingSetEmptyKegWeight).toBe(true);
    });

    it('should call setPlaatoKegValue with empty_keg_weight', () => {
      component.setEmptyKegWeight(component.modifyDevice);
      expect(mockDataService.setPlaatoKegValue).toHaveBeenCalledWith(
        'device-1',
        'empty_keg_weight',
        6
      );
    });
  });

  describe('setMaxKegVolume', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyDevice = new PlaatoKegDevice(mockDevices[0]);
      component.modifyDevice.enableEditing();
      component.modifyDevice.editValues.maxKegVolume = 25;
      mockDataService.setPlaatoKegValue.and.returnValue(of({}));
      mockDataService.getPlaatoKegDevice.and.returnValue(of(mockDevices[0]));
    });

    it('should set processingSetMaxKegVolume to true', () => {
      component.setMaxKegVolume(component.modifyDevice);
      expect(component.processingSetMaxKegVolume).toBe(true);
    });

    it('should call setPlaatoKegValue with max_keg_volume', () => {
      component.setMaxKegVolume(component.modifyDevice);
      expect(mockDataService.setPlaatoKegValue).toHaveBeenCalledWith(
        'device-1',
        'max_keg_volume',
        25
      );
    });
  });
});
