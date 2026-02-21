import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatIconRegistry } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DomSanitizer } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { BehaviorSubject, of, throwError } from 'rxjs';
import { filter } from 'rxjs/operators';

import { DataError, DataService } from '../_services/data.service';
import { SettingsService } from '../_services/settings.service';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;
  let mockIconRegistry: jasmine.SpyObj<MatIconRegistry>;
  let mockSanitizer: jasmine.SpyObj<DomSanitizer>;
  let mockActivatedRoute: any;

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', ['login']);
    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);
    mockIconRegistry = jasmine.createSpyObj('MatIconRegistry', ['addSvgIcon']);
    mockSanitizer = jasmine.createSpyObj('DomSanitizer', ['bypassSecurityTrustResourceUrl']);

    mockActivatedRoute = {
      queryParams: of({}),
    };

    mockSanitizer.bypassSecurityTrustResourceUrl.and.returnValue('safe-url');
    mockSettingsService.getSetting.and.returnValue(false);

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [LoginComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: Router, useValue: mockRouter },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
        { provide: MatSnackBar, useValue: mockSnackBar },
        { provide: MatIconRegistry, useValue: mockIconRegistry },
        { provide: DomSanitizer, useValue: mockSanitizer },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have loading set to false', () => {
      expect(component.loading).toBe(false);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have loginFormGroup defined', () => {
      expect(component.loginFormGroup).toBeTruthy();
    });

    it('should have email control', () => {
      expect(component.loginFormGroup.get('email')).toBeTruthy();
    });

    it('should have password control', () => {
      expect(component.loginFormGroup.get('password')).toBeTruthy();
    });
  });

  describe('constructor', () => {
    it('should register Google logo SVG icon', () => {
      expect(mockIconRegistry.addSvgIcon).toHaveBeenCalledWith('logo', 'safe-url');
    });

    it('should sanitize the icon URL', () => {
      expect(mockSanitizer.bypassSecurityTrustResourceUrl).toHaveBeenCalled();
    });
  });

  describe('ngOnInit', () => {
    it('should display error from query params', async () => {
      await TestBed.resetTestingModule();

      const activatedRouteWithError = {
        queryParams: of({ error: 'Session expired' }),
      };

      await TestBed.configureTestingModule({
        imports: [ReactiveFormsModule],
        declarations: [LoginComponent],
        providers: [
          { provide: DataService, useValue: mockDataService },
          { provide: SettingsService, useValue: mockSettingsService },
          { provide: Router, useValue: mockRouter },
          { provide: ActivatedRoute, useValue: activatedRouteWithError },
          { provide: MatSnackBar, useValue: mockSnackBar },
          { provide: MatIconRegistry, useValue: mockIconRegistry },
          { provide: DomSanitizer, useValue: mockSanitizer },
        ],
        schemas: [NO_ERRORS_SCHEMA],
      }).compileComponents();

      const newFixture = TestBed.createComponent(LoginComponent);
      newFixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Session expired', 'Close');
    });
  });

  describe('loginForm getter', () => {
    it('should return form controls', () => {
      const controls = component.loginForm;
      expect(controls['email']).toBeTruthy();
      expect(controls['password']).toBeTruthy();
    });
  });

  describe('form validation', () => {
    it('should be invalid when empty', () => {
      expect(component.loginFormGroup.valid).toBe(false);
    });

    it('should be valid with email and password', () => {
      component.loginFormGroup.get('email')?.setValue('test@example.com');
      component.loginFormGroup.get('password')?.setValue('password123');
      expect(component.loginFormGroup.valid).toBe(true);
    });

    it('should require email', () => {
      component.loginFormGroup.get('password')?.setValue('password123');
      expect(component.loginFormGroup.valid).toBe(false);
    });

    it('should require password', () => {
      component.loginFormGroup.get('email')?.setValue('test@example.com');
      expect(component.loginFormGroup.valid).toBe(false);
    });
  });

  describe('submit', () => {
    beforeEach(() => {
      component.email = 'test@example.com';
      component.password = 'password123';
    });

    it('should set processing to true when submitting', () => {
      // Use a subject that never emits to keep processing=true observable pending
      const pending$ = new BehaviorSubject<any>(null).asObservable().pipe(
        // Never actually emit - just keep the subscription open
        filter(() => false)
      );
      mockDataService.login.and.returnValue(pending$ as any);
      component.submit();
      expect(component.processing).toBe(true);
    });

    it('should call dataService.login with credentials', () => {
      // Use throwError to prevent window.location redirect
      const error: DataError = { message: 'Test', statusCode: 500 } as DataError;
      mockDataService.login.and.returnValue(throwError(() => error));
      component.submit();
      expect(mockDataService.login).toHaveBeenCalledWith('test@example.com', 'password123');
    });

    it('should display error for 400 status', () => {
      const error: DataError = { message: 'Bad request', statusCode: 400 } as DataError;
      mockDataService.login.and.returnValue(throwError(() => error));

      component.submit();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Bad request', 'Close');
    });

    it('should display invalid credentials error for 401 status', () => {
      const error: DataError = { message: 'Unauthorized', statusCode: 401 } as DataError;
      mockDataService.login.and.returnValue(throwError(() => error));

      component.submit();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error: Invalid username or password',
        'Close'
      );
    });

    it('should display unknown error for other status codes', () => {
      const error: DataError = { message: 'Server error', statusCode: 500 } as DataError;
      mockDataService.login.and.returnValue(throwError(() => error));

      component.submit();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error: An unknown error occurred trying to login.',
        'Close'
      );
    });

    it('should set processing to false on error', () => {
      const error: DataError = { message: 'Error', statusCode: 500 } as DataError;
      mockDataService.login.and.returnValue(throwError(() => error));

      component.submit();

      expect(component.processing).toBe(false);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('loginWithGoogle', () => {
    it('should be a function', () => {
      expect(typeof component.loginWithGoogle).toBe('function');
    });

    // Note: Can't easily test location.href changes in unit tests
  });

  describe('googleSSOEnabled getter', () => {
    it('should return false when setting is false', () => {
      mockSettingsService.getSetting.and.returnValue(false);
      expect(component.googleSSOEnabled).toBe(false);
    });

    it('should return true when setting is true', () => {
      mockSettingsService.getSetting.and.returnValue(true);
      expect(component.googleSSOEnabled).toBe(true);
    });

    it('should return false when setting is undefined', () => {
      mockSettingsService.getSetting.and.returnValue(undefined);
      expect(component.googleSSOEnabled).toBe(false);
    });

    it('should call getSetting with googleSSOEnabled', () => {
      component.googleSSOEnabled; /* eslint-disable-line @typescript-eslint/no-unused-expressions */
      expect(mockSettingsService.getSetting).toHaveBeenCalledWith('googleSSOEnabled');
    });
  });
});
