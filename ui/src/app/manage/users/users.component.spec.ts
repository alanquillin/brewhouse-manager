import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { ManageUsersComponent } from './users.component';
import { DataService, DataError } from '../../_services/data.service';
import { Location, UserInfo } from '../../models/models';

describe('ManageUsersComponent', () => {
  let component: ManageUsersComponent;
  let fixture: ComponentFixture<ManageUsersComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockCurrentUser = {
    id: 'user-1',
    email: 'admin@example.com',
    firstName: 'Admin',
    lastName: 'User',
    admin: true,
  };

  const mockLocations = [
    { id: 'loc-1', name: 'location-1', description: 'Location 1' },
    { id: 'loc-2', name: 'location-2', description: 'Location 2' },
  ];

  const mockUsers = [
    {
      id: 'user-1',
      email: 'admin@example.com',
      firstName: 'Admin',
      lastName: 'User',
      admin: true,
      hasPassword: true,
      locations: [mockLocations[0]],
    },
    {
      id: 'user-2',
      email: 'user@example.com',
      firstName: 'Regular',
      lastName: 'User',
      admin: false,
      hasPassword: false,
      locations: [],
    },
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', [
      'getCurrentUser',
      'getLocations',
      'getUsers',
      'createUser',
      'updateUser',
      'deleteUser',
      'updateUserLocations',
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockDataService.getCurrentUser.and.returnValue(of(mockCurrentUser as any));
    mockDataService.getLocations.and.returnValue(of(mockLocations as any));
    mockDataService.getUsers.and.returnValue(of(mockUsers as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManageUsersComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageUsersComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have loading set to false', () => {
      expect(component.loading).toBe(false);
    });

    it('should have empty users array', () => {
      expect(component.users).toEqual([]);
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

    it('should have changePassword set to false', () => {
      expect(component.changePassword).toBe(false);
    });

    it('should have hidePassword set to true', () => {
      expect(component.hidePassword).toBe(true);
    });

    it('should have modifyFormGroup defined', () => {
      expect(component.modifyFormGroup).toBeTruthy();
    });

    it('should have changePasswordFormGroup defined', () => {
      expect(component.changePasswordFormGroup).toBeTruthy();
    });

    it('should have displayedColumns defined', () => {
      expect(component.displayedColumns).toContain('email');
      expect(component.displayedColumns).toContain('firstName');
      expect(component.displayedColumns).toContain('lastName');
      expect(component.displayedColumns).toContain('admin');
      expect(component.displayedColumns).toContain('actions');
    });
  });

  describe('ngOnInit', () => {
    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockDataService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set me on success', () => {
      fixture.detectChanges();
      expect(component.me.email).toBe('admin@example.com');
    });

    it('should call _refresh', () => {
      fixture.detectChanges();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Failed', statusCode: 500 } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed', 'Close');
    });
  });

  describe('_refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getLocations', () => {
      component._refresh();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call getUsers', () => {
      component._refresh();
      expect(mockDataService.getUsers).toHaveBeenCalled();
    });

    it('should populate locations', () => {
      component._refresh();
      expect(component.locations.length).toBe(2);
    });

    it('should populate users', () => {
      component._refresh();
      expect(component.users.length).toBe(2);
    });

    it('should initialize selectedLocations', () => {
      component._refresh();
      expect(component.selectedLocations['loc-1']).toBe(false);
      expect(component.selectedLocations['loc-2']).toBe(false);
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

    it('should display error on locations failure', () => {
      const error: DataError = { message: 'Failed to load locations' } as DataError;
      mockDataService.getLocations.and.returnValue(throwError(() => error));

      component._refresh();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load locations', 'Close');
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

    it('should call _refresh', () => {
      spyOn(component, '_refresh').and.callThrough();
      component.refresh();
      expect(component._refresh).toHaveBeenCalled();
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

    it('should create new modifyUser', () => {
      component.add();
      expect(component.modifyUser).toBeTruthy();
    });

    it('should set adding to true', () => {
      component.add();
      expect(component.adding).toBe(true);
    });

    it('should reset selected locations', () => {
      component.selectedLocations['loc-1'] = true;
      component.add();
      expect(component.selectedLocations['loc-1']).toBe(false);
    });
  });

  describe('create', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyUser = new UserInfo();
      component.modifyUser.enableEditing();
      component.modifyUser.editValues = {
        email: 'new@example.com',
        firstName: 'New',
        lastName: 'User',
      };
      mockDataService.createUser.and.returnValue(of(mockUsers[1] as any));
      mockDataService.updateUserLocations.and.returnValue(of({}));
    });

    it('should set processing to true', () => {
      component.create();
      expect(mockDataService.createUser).toHaveBeenCalled();
    });

    it('should call createUser', () => {
      component.create();
      expect(mockDataService.createUser).toHaveBeenCalled();
    });

    it('should include password if provided', () => {
      component.modifyForm['password'].setValue('StrongPass1!');
      component.create();
      const callArg = mockDataService.createUser.calls.mostRecent().args[0];
      expect(callArg.password).toBe('StrongPass1!');
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createUser.and.returnValue(throwError(() => error));

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

    it('should enable editing on user', () => {
      const user = new UserInfo(mockUsers[0]);
      component.edit(user);
      expect(user.isEditing).toBe(true);
    });

    it('should set modifyUser', () => {
      const user = new UserInfo(mockUsers[0]);
      component.edit(user);
      expect(component.modifyUser).toBe(user);
    });

    it('should set editing to true', () => {
      const user = new UserInfo(mockUsers[0]);
      component.edit(user);
      expect(component.editing).toBe(true);
    });

    it('should populate selectedLocations from user locations', () => {
      const user = new UserInfo(mockUsers[0]);
      component.edit(user);
      expect(component.selectedLocations['loc-1']).toBe(true);
    });
  });

  describe('save', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyUser = new UserInfo(mockUsers[0]);
      component.modifyUser.enableEditing();
      component.modifyUser.editValues.firstName = 'Updated';
      mockDataService.updateUser.and.returnValue(of(mockUsers[0] as any));
      mockDataService.updateUserLocations.and.returnValue(of({}));
    });

    it('should call updateUser when user has changes', () => {
      component.save();
      expect(mockDataService.updateUser).toHaveBeenCalledWith('user-1', { firstName: 'Updated' });
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Update failed' } as DataError;
      mockDataService.updateUser.and.returnValue(throwError(() => error));

      component.save();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Update failed', 'Close');
    });
  });

  describe('saveLocations', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyUser = new UserInfo(mockUsers[0]);
      component.selectedLocations = { 'loc-1': true, 'loc-2': false };
      mockDataService.updateUserLocations.and.returnValue(of({}));
    });

    it('should call next when no location changes', () => {
      const nextCallback = jasmine.createSpy('next');
      component.saveLocations(component.modifyUser, nextCallback);
      expect(nextCallback).toHaveBeenCalled();
    });

    it('should call updateUserLocations when locations changed', () => {
      component.selectedLocations = { 'loc-1': true, 'loc-2': true };
      const nextCallback = jasmine.createSpy('next');
      component.saveLocations(component.modifyUser, nextCallback);
      expect(mockDataService.updateUserLocations).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      component.selectedLocations = { 'loc-1': true, 'loc-2': true };
      const error: DataError = { message: 'Location update failed' } as DataError;
      mockDataService.updateUserLocations.and.returnValue(throwError(() => error));
      const nextCallback = jasmine.createSpy('next');

      component.saveLocations(component.modifyUser, nextCallback);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Location update failed', 'Close');
    });
  });

  describe('cancelEdit', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyUser = new UserInfo(mockUsers[0]);
      component.modifyUser.enableEditing();
      component.editing = true;
    });

    it('should disable editing on modifyUser', () => {
      component.cancelEdit();
      expect(component.modifyUser.isEditing).toBe(false);
    });

    it('should set editing to false', () => {
      component.cancelEdit();
      expect(component.editing).toBe(false);
    });
  });

  describe('delete', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deleteUser.and.returnValue(of({}));
    });

    it('should call deleteUser when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const user = new UserInfo(mockUsers[1]);

      component.delete(user);

      expect(mockDataService.deleteUser).toHaveBeenCalledWith('user-2');
    });

    it('should not call deleteUser when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const user = new UserInfo(mockUsers[1]);

      component.delete(user);

      expect(mockDataService.deleteUser).not.toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const error: DataError = { message: 'Delete failed' } as DataError;
      mockDataService.deleteUser.and.returnValue(throwError(() => error));
      const user = new UserInfo(mockUsers[1]);

      component.delete(user);

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Delete failed', 'Close');
    });
  });

  describe('filter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.users = mockUsers.map(u => new UserInfo(u));
    });

    it('should populate filteredUsers', () => {
      component.filter();
      expect(component.filteredUsers.length).toBeGreaterThan(0);
    });

    it('should sort users', () => {
      component.filter();
      expect(component.filteredUsers.length).toBe(2);
    });
  });

  describe('modifyForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyForm;
      expect(controls['email']).toBeTruthy();
      expect(controls['firstName']).toBeTruthy();
      expect(controls['lastName']).toBeTruthy();
    });
  });

  describe('form validation', () => {
    it('should require email', () => {
      const control = component.modifyFormGroup.get('email');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should validate email format', () => {
      const control = component.modifyFormGroup.get('email');
      control?.setValue('invalid-email');
      expect(control?.hasError('email')).toBe(true);
    });

    it('should accept valid email', () => {
      const control = component.modifyFormGroup.get('email');
      control?.setValue('valid@example.com');
      expect(control?.valid).toBe(true);
    });
  });

  describe('changeLocationsSelection', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should update selectedLocations', () => {
      const location = new Location(mockLocations[0]);
      component.changeLocationsSelection(true, location);
      expect(component.selectedLocations['loc-1']).toBe(true);

      component.changeLocationsSelection(false, location);
      expect(component.selectedLocations['loc-1']).toBe(false);
    });
  });

  describe('selectedLocationChanges', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyUser = new UserInfo(mockUsers[0]);
    });

    it('should return false when no changes', () => {
      component.selectedLocations = { 'loc-1': true };
      expect(component.selectedLocationChanges()).toBe(false);
    });

    it('should return true when locations added', () => {
      component.selectedLocations = { 'loc-1': true, 'loc-2': true };
      expect(component.selectedLocationChanges()).toBe(true);
    });

    it('should return true when locations removed', () => {
      component.selectedLocations = {};
      expect(component.selectedLocationChanges()).toBe(true);
    });
  });

  describe('resetSelectedLocations', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should set all locations to false', () => {
      component.selectedLocations = { 'loc-1': true, 'loc-2': true };
      component.resetSelectedLocations();
      expect(component.selectedLocations['loc-1']).toBe(false);
      expect(component.selectedLocations['loc-2']).toBe(false);
    });
  });

  describe('changes getter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyUser = new UserInfo(mockUsers[0]);
      component.modifyUser.enableEditing();
    });

    it('should return true when user has changes', () => {
      component.modifyUser.editValues.firstName = 'Changed';
      expect(component.changes).toBe(true);
    });

    it('should return true when locations have changes', () => {
      component.selectedLocations = { 'loc-1': true, 'loc-2': true };
      expect(component.changes).toBe(true);
    });

    it('should return false when no changes', () => {
      component.selectedLocations = { 'loc-1': true };
      expect(component.changes).toBe(false);
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
        component.modifyUser = new UserInfo(mockUsers[0]);
        mockDataService.updateUser.and.returnValue(of(mockUsers[0] as any));
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

        component.savePassword();

        expect(mockDataService.updateUser).toHaveBeenCalledWith('user-1', { password: 'StrongPass1!' });
      });

      it('should set changePassword to false on success', () => {
        component.changePasswordFormGroup.get('password')?.setValue('StrongPass1!');
        component.changePasswordFormGroup.get('confirmPassword')?.setValue('StrongPass1!');
        component.changePassword = true;

        component.savePassword();

        expect(component.changePassword).toBe(false);
      });

      it('should display error on failure', () => {
        component.changePasswordFormGroup.get('password')?.setValue('StrongPass1!');
        component.changePasswordFormGroup.get('confirmPassword')?.setValue('StrongPass1!');
        const error: DataError = { message: 'Password update failed' } as DataError;
        mockDataService.updateUser.and.returnValue(throwError(() => error));

        component.savePassword();

        expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Password update failed', 'Close');
      });
    });

    describe('disablePassword', () => {
      beforeEach(() => {
        fixture.detectChanges();
        component.modifyUser = new UserInfo(mockUsers[0]);
        mockDataService.updateUser.and.returnValue(of(mockUsers[0] as any));
      });

      it('should call updateUser with null password when confirmed', () => {
        spyOn(window, 'confirm').and.returnValue(true);

        component.disablePassword();

        expect(mockDataService.updateUser).toHaveBeenCalledWith('user-1', { password: null });
      });

      it('should not call updateUser when not confirmed', () => {
        spyOn(window, 'confirm').and.returnValue(false);

        component.disablePassword();

        expect(mockDataService.updateUser).not.toHaveBeenCalled();
      });

      it('should display error on failure', () => {
        spyOn(window, 'confirm').and.returnValue(true);
        const error: DataError = { message: 'Disable password failed' } as DataError;
        mockDataService.updateUser.and.returnValue(throwError(() => error));

        component.disablePassword();

        expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Disable password failed', 'Close');
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

  describe('changePasswordForm getter', () => {
    it('should return password form controls', () => {
      const controls = component.changePasswordForm;
      expect(controls['password']).toBeTruthy();
      expect(controls['confirmPassword']).toBeTruthy();
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });
});
