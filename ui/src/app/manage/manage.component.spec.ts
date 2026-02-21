import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { CurrentUserService } from '../_services/current-user.service';
import { DataError } from '../_services/data.service';
import { SettingsService } from '../_services/settings.service';
import { ManageComponent } from './manage.component';

describe('ManageComponent', () => {
  let component: ManageComponent;
  let fixture: ComponentFixture<ManageComponent>;
  let mockCurrentUserService: jasmine.SpyObj<CurrentUserService>;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockUserInfo = {
    id: 'user-1',
    email: 'test@example.com',
    firstName: 'John',
    lastName: 'Doe',
    admin: true,
    apiKey: '',
    hasPassword: true,
  };

  beforeEach(async () => {
    mockCurrentUserService = jasmine.createSpyObj('CurrentUserService', ['getCurrentUser']);
    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockCurrentUserService.getCurrentUser.and.returnValue(of(mockUserInfo as any));
    mockSettingsService.getSetting.and.returnValue(false);

    await TestBed.configureTestingModule({
      declarations: [ManageComponent],
      providers: [
        { provide: CurrentUserService, useValue: mockCurrentUserService },
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have title set to Manage Brewhouse', () => {
      expect(component.title).toBe('Manage Brewhouse');
    });

    it('should have isLoading set to false initially', () => {
      expect(component.isLoading).toBe(false);
    });
  });

  describe('ngOnInit', () => {
    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on success', () => {
      fixture.detectChanges();
      expect(component.userInfo?.email).toBe('test@example.com');
    });

    it('should set userInfo to null when not logged in', () => {
      mockCurrentUserService.getCurrentUser.and.returnValue(of(null));
      fixture.detectChanges();
      expect(component.userInfo).toBeNull();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load', statusCode: 500 } as DataError;
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load', 'Close');
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('admin getter', () => {
    it('should return false when userInfo is null', () => {
      component.userInfo = null as any;
      expect(component.admin).toBe(false);
    });

    it('should return false when userInfo is undefined', () => {
      component.userInfo = undefined as any;
      expect(component.admin).toBe(false);
    });

    it('should return true when user is admin', () => {
      fixture.detectChanges();
      expect(component.admin).toBe(true);
    });

    it('should return false when user is not admin', () => {
      const nonAdminUser = { ...mockUserInfo, admin: false };
      mockCurrentUserService.getCurrentUser.and.returnValue(of(nonAdminUser as any));
      fixture.detectChanges();
      expect(component.admin).toBe(false);
    });
  });

  describe('plaatoKegEnabled getter', () => {
    it('should return false when setting is false', () => {
      mockSettingsService.getSetting.and.returnValue(false);
      expect(component.plaatoKegEnabled).toBe(false);
    });

    it('should return true when setting is true', () => {
      mockSettingsService.getSetting.and.returnValue(true);
      expect(component.plaatoKegEnabled).toBe(true);
    });

    it('should return false when setting is undefined', () => {
      mockSettingsService.getSetting.and.returnValue(undefined);
      expect(component.plaatoKegEnabled).toBe(false);
    });

    it('should call getSetting with correct key', () => {
      component.plaatoKegEnabled; /* eslint-disable-line @typescript-eslint/no-unused-expressions */
      expect(mockSettingsService.getSetting).toHaveBeenCalledWith('plaato_keg_devices.enabled');
    });
  });

  describe('goto', () => {
    it('should be a function', () => {
      expect(typeof component.goto).toBe('function');
    });

    // Note: Can't easily test window.location.href changes in unit tests
  });
});
