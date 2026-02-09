import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { MatMenuModule } from '@angular/material/menu';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { HeaderComponent } from './header.component';
import { DataService, DataError } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';
import { UserInfo } from '../../models/models';

describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockUserInfo = new UserInfo({
    firstName: 'John',
    lastName: 'Doe',
    admin: true,
  });

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', ['getCurrentUser']);
    mockDataService.getCurrentUser.and.returnValue(of(mockUserInfo));

    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting']);
    mockSettingsService.getSetting.and.returnValue(false);

    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    await TestBed.configureTestingModule({
      imports: [MatMenuModule],
      declarations: [HeaderComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HeaderComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('ngOnInit', () => {
    it('should fetch current user on init', () => {
      fixture.detectChanges();

      expect(mockDataService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on successful response', () => {
      fixture.detectChanges();

      expect(component.userInfo).toEqual(mockUserInfo);
    });

    it('should display error on non-401 error', () => {
      const error: DataError = { statusCode: 500, message: 'Server error' } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Server error', 'Close');
    });

    it('should not display error on 401 error', () => {
      const error: DataError = { statusCode: 401, message: 'Unauthorized' } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).not.toHaveBeenCalled();
    });
  });

  describe('title input', () => {
    it('should have default empty title', () => {
      fixture.detectChanges();
      expect(component.title).toBe('');
    });

    it('should accept title input', () => {
      component.title = 'My App';
      fixture.detectChanges();
      expect(component.title).toBe('My App');
    });
  });

  describe('name getter', () => {
    it('should return full name when userInfo is set', () => {
      fixture.detectChanges();

      expect(component.name).toBe('John Doe');
    });

    it('should return UNKNOWN when userInfo is null', () => {
      mockDataService.getCurrentUser.and.returnValue(of(null as unknown as UserInfo));
      fixture.detectChanges();

      // Need to explicitly set to null after init
      component.userInfo = null as unknown as UserInfo;

      expect(component.name).toBe('UNKNOWN');
    });

    it('should return UNKNOWN when userInfo is undefined', () => {
      mockDataService.getCurrentUser.and.returnValue(of(undefined as unknown as UserInfo));
      fixture.detectChanges();

      component.userInfo = undefined as unknown as UserInfo;

      expect(component.name).toBe('UNKNOWN');
    });
  });

  describe('admin getter', () => {
    it('should return true when user is admin', () => {
      fixture.detectChanges();

      expect(component.admin).toBe(true);
    });

    it('should return false when user is not admin', () => {
      const nonAdminUser = new UserInfo({ firstName: 'Jane', lastName: 'Doe', admin: false });
      mockDataService.getCurrentUser.and.returnValue(of(nonAdminUser));
      fixture.detectChanges();

      expect(component.admin).toBe(false);
    });

    it('should return false when userInfo is null', () => {
      mockDataService.getCurrentUser.and.returnValue(of(null as unknown as UserInfo));
      fixture.detectChanges();

      component.userInfo = null as unknown as UserInfo;

      expect(component.admin).toBe(false);
    });

    it('should return false when userInfo is undefined', () => {
      fixture.detectChanges();
      component.userInfo = undefined as unknown as UserInfo;

      expect(component.admin).toBe(false);
    });
  });

  describe('plaatoKegEnabled getter', () => {
    it('should return true when setting is enabled', () => {
      mockSettingsService.getSetting.and.returnValue(true);
      fixture.detectChanges();

      expect(component.plaatoKegEnabled).toBe(true);
      expect(mockSettingsService.getSetting).toHaveBeenCalledWith('plaato_keg_devices.enabled');
    });

    it('should return false when setting is disabled', () => {
      mockSettingsService.getSetting.and.returnValue(false);
      fixture.detectChanges();

      expect(component.plaatoKegEnabled).toBe(false);
    });

    it('should return false when setting is undefined', () => {
      mockSettingsService.getSetting.and.returnValue(undefined);
      fixture.detectChanges();

      expect(component.plaatoKegEnabled).toBe(false);
    });
  });

  describe('logout', () => {
    it('should call goto with logout path', () => {
      fixture.detectChanges();
      spyOn(component, 'goto');

      component.logout();

      expect(component.goto).toHaveBeenCalledWith('logout');
    });
  });

  describe('goto', () => {
    it('should be a method that can be called', () => {
      fixture.detectChanges();
      // We can't easily test window.location.href changes in unit tests
      // Just verify the method exists and is callable
      expect(typeof component.goto).toBe('function');
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      fixture.detectChanges();

      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });
});
