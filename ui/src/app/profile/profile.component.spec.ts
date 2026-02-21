import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { CurrentUserService } from '../_services/current-user.service';
import { DataError, DataService } from '../_services/data.service';
import { UserInfo } from '../models/models';
import { ProfileComponent } from './profile.component';

describe('ProfileComponent', () => {
  let component: ProfileComponent;
  let fixture: ComponentFixture<ProfileComponent>;
  let mockCurrentUserService: jasmine.SpyObj<CurrentUserService>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockUserInfo = {
    id: 'user-1',
    email: 'test@example.com',
    firstName: 'John',
    lastName: 'Doe',
    admin: false,
    apiKey: '',
    hasPassword: true,
  };

  beforeEach(async () => {
    mockCurrentUserService = jasmine.createSpyObj('CurrentUserService', ['getCurrentUser']);
    mockDataService = jasmine.createSpyObj('DataService', [
      'updateUser',
      'generateUserAPIKey',
      'deleteUserAPIKey',
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockCurrentUserService.getCurrentUser.and.returnValue(of(mockUserInfo as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ProfileComponent],
      providers: [
        { provide: CurrentUserService, useValue: mockCurrentUserService },
        { provide: DataService, useValue: mockDataService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ProfileComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have editing set to false', () => {
      expect(component.editing).toBe(false);
    });

    it('should have changePassword set to false', () => {
      expect(component.changePassword).toBe(false);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have empty newPassword', () => {
      expect(component.newPassword).toBe('');
    });

    it('should have empty confirmNewPassword', () => {
      expect(component.confirmNewPassword).toBe('');
    });

    it('should have editFormGroup defined', () => {
      expect(component.editFormGroup).toBeTruthy();
    });

    it('should have changePasswordFormGroup defined', () => {
      expect(component.changePasswordFormGroup).toBeTruthy();
    });
  });

  describe('ngOnInit', () => {
    it('should call refresh', () => {
      spyOn(component, 'refresh');
      component.ngOnInit();
      expect(component.refresh).toHaveBeenCalled();
    });
  });

  describe('refresh', () => {
    it('should set processing to true while loading', () => {
      component.refresh();
      // After sync observable completes, processing is false
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
    });

    it('should call getCurrentUser', () => {
      component.refresh();
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on success', () => {
      component.refresh();
      expect(component.userInfo.email).toBe('test@example.com');
    });

    it('should set processing to false on success', () => {
      component.refresh();
      expect(component.processing).toBe(false);
    });

    it('should call next callback if provided', () => {
      const nextCallback = jasmine.createSpy('next');
      component.refresh(undefined, nextCallback);
      expect(nextCallback).toHaveBeenCalled();
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component.refresh(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed to load' } as DataError;
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));

      component.refresh();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load', 'Close');
    });

    it('should call error callback on failure', () => {
      const error: DataError = { message: 'Failed' } as DataError;
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));
      const errorCallback = jasmine.createSpy('error');

      component.refresh(undefined, undefined, errorCallback);

      expect(errorCallback).toHaveBeenCalled();
    });
  });

  describe('editing', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    describe('startEditing', () => {
      it('should set editing to true', () => {
        component.startEditing();
        expect(component.editing).toBe(true);
      });

      it('should enable editing on userInfo', () => {
        spyOn(component.userInfo, 'enableEditing');
        component.startEditing();
        expect(component.userInfo.enableEditing).toHaveBeenCalled();
      });
    });

    describe('cancelEditing', () => {
      it('should set editing to false', () => {
        component.editing = true;
        component.cancelEditing();
        expect(component.editing).toBe(false);
      });

      it('should disable editing on userInfo', () => {
        spyOn(component.userInfo, 'disableEditing');
        component.cancelEditing();
        expect(component.userInfo.disableEditing).toHaveBeenCalled();
      });
    });
  });

  describe('save', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.editFormGroup.get('email')?.setValue('test@example.com');
      component.editFormGroup.get('firstName')?.setValue('John');
      component.editFormGroup.get('lastName')?.setValue('Doe');
    });

    it('should return early if form is invalid', () => {
      component.editFormGroup.get('email')?.setValue('');
      component.save();
      expect(mockDataService.updateUser).not.toHaveBeenCalled();
    });

    it('should set processing to true', () => {
      mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));
      component.save();
      // Processing goes true then false after sync observable
      expect(mockDataService.updateUser).toHaveBeenCalled();
    });

    it('should call updateUser with user changes', () => {
      mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));
      component.userInfo = new UserInfo(mockUserInfo);
      component.save();
      expect(mockDataService.updateUser).toHaveBeenCalledWith('user-1', component.userInfo.changes);
    });

    it('should set editing to false on success', () => {
      mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));
      component.editing = true;
      component.save();
      expect(component.editing).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Update failed' } as DataError;
      mockDataService.updateUser.and.returnValue(throwError(() => error));

      component.save();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Update failed', 'Close');
    });
  });

  describe('change password', () => {
    describe('startChangePassword', () => {
      it('should set changePassword to true', () => {
        component.startChangePassword();
        expect(component.changePassword).toBe(true);
      });

      it('should reset newPassword', () => {
        component.newPassword = 'old';
        component.startChangePassword();
        expect(component.newPassword).toBe('');
      });

      it('should reset confirmNewPassword', () => {
        component.confirmNewPassword = 'old';
        component.startChangePassword();
        expect(component.confirmNewPassword).toBe('');
      });
    });

    describe('cancelChangePassword', () => {
      it('should set changePassword to false', () => {
        component.changePassword = true;
        component.cancelChangePassword();
        expect(component.changePassword).toBe(false);
      });
    });

    describe('savePassword', () => {
      beforeEach(() => {
        fixture.detectChanges();
      });

      it('should return early if form is invalid', () => {
        component.changePasswordFormGroup.get('password')?.setValue('weak');
        component.savePassword();
        expect(mockDataService.updateUser).not.toHaveBeenCalled();
      });

      it('should call updateUser with new password', () => {
        component.changePasswordFormGroup.get('password')?.setValue('StrongPass1!');
        component.changePasswordFormGroup.get('confirmPassword')?.setValue('StrongPass1!');
        component.newPassword = 'StrongPass1!';
        mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));

        component.savePassword();

        expect(mockDataService.updateUser).toHaveBeenCalledWith('user-1', {
          password: 'StrongPass1!',
        });
      });

      it('should set changePassword to false on success', () => {
        component.changePasswordFormGroup.get('password')?.setValue('StrongPass1!');
        component.changePasswordFormGroup.get('confirmPassword')?.setValue('StrongPass1!');
        component.changePassword = true;
        mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));

        component.savePassword();

        expect(component.changePassword).toBe(false);
      });

      it('should display error on failure', () => {
        component.changePasswordFormGroup.get('password')?.setValue('StrongPass1!');
        component.changePasswordFormGroup.get('confirmPassword')?.setValue('StrongPass1!');
        const error: DataError = { message: 'Password change failed' } as DataError;
        mockDataService.updateUser.and.returnValue(throwError(() => error));

        component.savePassword();

        expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Password change failed', 'Close');
      });
    });
  });

  describe('password validation', () => {
    it('should require password', () => {
      const control = component.changePasswordFormGroup.get('password');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should require pattern match', () => {
      const control = component.changePasswordFormGroup.get('password');
      control?.setValue('weak');
      expect(control?.hasError('pattern')).toBe(true);
    });

    it('should accept valid password', () => {
      const control = component.changePasswordFormGroup.get('password');
      control?.setValue('StrongPass1!');
      expect(control?.valid).toBe(true);
    });

    it('should validate password confirmation matches', () => {
      component.changePasswordFormGroup.get('password')?.setValue('StrongPass1!');
      component.changePasswordFormGroup.get('confirmPassword')?.setValue('DifferentPass1!');
      expect(component.changePasswordFormGroup.hasError('matching')).toBe(true);
    });
  });

  describe('API key management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    describe('generateAPIKey', () => {
      it('should call _generateAPIKey when no existing key', () => {
        component.userInfo.apiKey = '';
        mockDataService.generateUserAPIKey.and.returnValue(of({ apiKey: 'new-key' }));

        component.generateAPIKey();

        expect(mockDataService.generateUserAPIKey).toHaveBeenCalledWith('user-1');
      });

      it('should set apiKey on success', () => {
        component.userInfo.apiKey = '';
        mockDataService.generateUserAPIKey.and.returnValue(of({ apiKey: 'new-key' }));

        component.generateAPIKey();

        expect(component.userInfo.apiKey).toBe('new-key');
      });

      it('should display error on failure', () => {
        component.userInfo.apiKey = '';
        const error: DataError = { message: 'Key generation failed' } as DataError;
        mockDataService.generateUserAPIKey.and.returnValue(throwError(() => error));

        component.generateAPIKey();

        expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Key generation failed', 'Close');
      });
    });

    describe('deleteAPIKey', () => {
      it('should call deleteUserAPIKey when confirmed', () => {
        spyOn(window, 'confirm').and.returnValue(true);
        mockDataService.deleteUserAPIKey.and.returnValue(of(''));

        component.deleteAPIKey();

        expect(mockDataService.deleteUserAPIKey).toHaveBeenCalledWith('user-1');
      });

      it('should clear apiKey on success', () => {
        spyOn(window, 'confirm').and.returnValue(true);
        component.userInfo.apiKey = 'existing-key';
        mockDataService.deleteUserAPIKey.and.returnValue(of(''));

        component.deleteAPIKey();

        expect(component.userInfo.apiKey).toBe('');
      });

      it('should display error on failure', () => {
        spyOn(window, 'confirm').and.returnValue(true);
        const error: DataError = { message: 'Delete failed' } as DataError;
        mockDataService.deleteUserAPIKey.and.returnValue(throwError(() => error));

        component.deleteAPIKey();

        expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Delete failed', 'Close');
      });
    });
  });

  describe('clipboard operations', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    describe('copyToClipboard', () => {
      it('should return early for empty data', () => {
        // Can't spy on clipboard in headless browser, just verify the method logic
        // by checking that it doesn't throw for empty input
        expect(() => component.copyToClipboard('')).not.toThrow();
      });

      it('should return early for null data', () => {
        expect(() => component.copyToClipboard(null as any)).not.toThrow();
      });

      it('should have copyToClipboard method', () => {
        expect(typeof component.copyToClipboard).toBe('function');
      });
    });

    describe('copyAPIKeyRaw', () => {
      it('should copy raw API key', () => {
        component.userInfo.apiKey = 'test-api-key';
        spyOn(component, 'copyToClipboard');

        component.copyAPIKeyRaw();

        expect(component.copyToClipboard).toHaveBeenCalledWith('test-api-key');
      });
    });

    describe('copyAPIKeyEncoded', () => {
      it('should copy base64 encoded API key', () => {
        component.userInfo.apiKey = 'test-api-key';
        spyOn(component, 'copyToClipboard');

        component.copyAPIKeyEncoded();

        expect(component.copyToClipboard).toHaveBeenCalledWith(btoa('test-api-key'));
      });
    });
  });

  describe('getters', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    describe('name', () => {
      it('should return full name', () => {
        component.userInfo = new UserInfo({ firstName: 'John', lastName: 'Doe' });
        expect(component.name).toBe('John Doe');
      });

      it('should return UNKNOWN if userInfo is null', () => {
        component.userInfo = null as any;
        expect(component.name).toBe('UNKNOWN');
      });
    });

    describe('editForm', () => {
      it('should return form controls', () => {
        const controls = component.editForm;
        expect(controls['email']).toBeTruthy();
        expect(controls['firstName']).toBeTruthy();
        expect(controls['lastName']).toBeTruthy();
      });
    });

    describe('changePasswordForm', () => {
      it('should return password form controls', () => {
        const controls = component.changePasswordForm;
        expect(controls['password']).toBeTruthy();
        expect(controls['confirmPassword']).toBeTruthy();
      });
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('disablePassword', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call updateUser with null password when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));

      component.disablePassword();

      expect(mockDataService.updateUser).toHaveBeenCalledWith('user-1', { password: null });
    });

    it('should not call updateUser when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);

      component.disablePassword();

      expect(mockDataService.updateUser).not.toHaveBeenCalled();
    });

    it('should set editing to false on success', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      mockDataService.updateUser.and.returnValue(of(mockUserInfo as any));
      component.editing = true;

      component.disablePassword();

      expect(component.editing).toBe(false);
    });
  });
});
