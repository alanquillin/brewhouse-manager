import { TestBed } from '@angular/core/testing';
import { EventEmitter } from '@angular/core';
import { of, throwError } from 'rxjs';

import { CurrentUserService } from './current-user.service';
import { DataService, DataError } from './data.service';
import { UserInfo } from '../models/models';

describe('CurrentUserService', () => {
  let service: CurrentUserService;
  let mockDataService: jasmine.SpyObj<DataService>;
  let unauthorizedEmitter: EventEmitter<DataError>;

  const mockUserInfo: any = {
    id: 'user-1',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    admin: true,
    locations: [{ id: 'loc-1', name: 'Location 1' }],
  };

  beforeEach(() => {
    unauthorizedEmitter = new EventEmitter<DataError>();
    mockDataService = jasmine.createSpyObj('DataService', ['getCurrentUser'], {
      unauthorized: unauthorizedEmitter,
    });
    mockDataService.getCurrentUser.and.returnValue(of(mockUserInfo as UserInfo));

    TestBed.configureTestingModule({
      providers: [CurrentUserService, { provide: DataService, useValue: mockDataService }],
    });
    service = TestBed.inject(CurrentUserService);
  });

  afterEach(() => {
    service.ngOnDestroy();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have currentUser$ as null initially', (done: DoneFn) => {
      service.currentUser$.subscribe(user => {
        expect(user).toBeNull();
        done();
      });
    });

    it('should have loading$ as false initially', (done: DoneFn) => {
      service.loading$.subscribe(loading => {
        expect(loading).toBe(false);
        done();
      });
    });

    it('should have loaded$ as false initially', (done: DoneFn) => {
      service.loaded$.subscribe(loaded => {
        expect(loaded).toBe(false);
        done();
      });
    });

    it('should return null from getUser() initially', () => {
      expect(service.getUser()).toBeNull();
    });

    it('should return false from isLoaded() initially', () => {
      expect(service.isLoaded()).toBe(false);
    });
  });

  describe('getCurrentUser', () => {
    it('should call dataService.getCurrentUser on first call', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        expect(mockDataService.getCurrentUser).toHaveBeenCalled();
        done();
      });
    });

    it('should pass ignoreUnauthorized=true to dataService.getCurrentUser', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        expect(mockDataService.getCurrentUser).toHaveBeenCalledWith(true);
        done();
      });
    });

    it('should return user info from API', (done: DoneFn) => {
      service.getCurrentUser().subscribe(user => {
        expect(user).toEqual(mockUserInfo as UserInfo);
        done();
      });
    });

    it('should cache the user after first call', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        mockDataService.getCurrentUser.calls.reset();

        service.getCurrentUser().subscribe(user => {
          expect(mockDataService.getCurrentUser).not.toHaveBeenCalled();
          expect(user).toEqual(mockUserInfo as UserInfo);
          done();
        });
      });
    });

    it('should set loaded to true after successful load', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        expect(service.isLoaded()).toBe(true);
        done();
      });
    });

    it('should update getUser() after load', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        expect(service.getUser()).toEqual(mockUserInfo as UserInfo);
        done();
      });
    });

    it('should return null for 401 error (not logged in)', (done: DoneFn) => {
      const error = new DataError('Unauthorized', 401, 'Unauthorized');
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      service.getCurrentUser().subscribe(user => {
        expect(user).toBeNull();
        done();
      });
    });

    it('should set loaded to true even on 401 error', (done: DoneFn) => {
      const error = new DataError('Unauthorized', 401, 'Unauthorized');
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      service.getCurrentUser().subscribe(() => {
        expect(service.isLoaded()).toBe(true);
        done();
      });
    });

    it('should throw non-401 errors', (done: DoneFn) => {
      const error = new DataError('Server error', 500, 'Internal Server Error');
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      service.getCurrentUser().subscribe({
        error: err => {
          expect(err.statusCode).toBe(500);
          done();
        },
      });
    });
  });

  describe('refresh', () => {
    it('should call dataService.getCurrentUser', (done: DoneFn) => {
      service.refresh().subscribe(() => {
        expect(mockDataService.getCurrentUser).toHaveBeenCalled();
        done();
      });
    });

    it('should update cached user with new data', (done: DoneFn) => {
      // First load
      service.getCurrentUser().subscribe(() => {
        const updatedUser: any = { ...mockUserInfo, firstName: 'Updated' };
        mockDataService.getCurrentUser.and.returnValue(of(updatedUser as UserInfo));

        // Refresh
        service.refresh().subscribe(user => {
          expect(user?.firstName).toBe('Updated');
          expect(service.getUser()?.firstName).toBe('Updated');
          done();
        });
      });
    });

    it('should call API even if already loaded', (done: DoneFn) => {
      // First load
      service.getCurrentUser().subscribe(() => {
        mockDataService.getCurrentUser.calls.reset();

        // Refresh should call API again
        service.refresh().subscribe(() => {
          expect(mockDataService.getCurrentUser).toHaveBeenCalled();
          done();
        });
      });
    });
  });

  describe('clear', () => {
    it('should set user to null', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        service.clear();
        expect(service.getUser()).toBeNull();
        done();
      });
    });

    it('should set loaded to false', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        service.clear();
        expect(service.isLoaded()).toBe(false);
        done();
      });
    });

    it('should trigger new API call on next getCurrentUser', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        service.clear();
        mockDataService.getCurrentUser.calls.reset();

        service.getCurrentUser().subscribe(() => {
          expect(mockDataService.getCurrentUser).toHaveBeenCalled();
          done();
        });
      });
    });
  });

  describe('unauthorized event', () => {
    it('should clear cached data when unauthorized event is emitted', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        expect(service.isLoaded()).toBe(true);
        expect(service.getUser()).not.toBeNull();

        // Emit unauthorized event
        unauthorizedEmitter.emit(new DataError('Unauthorized', 401, 'Unauthorized'));

        expect(service.isLoaded()).toBe(false);
        expect(service.getUser()).toBeNull();
        done();
      });
    });

    it('should trigger new API call after unauthorized event', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        unauthorizedEmitter.emit(new DataError('Unauthorized', 401, 'Unauthorized'));
        mockDataService.getCurrentUser.calls.reset();

        service.getCurrentUser().subscribe(() => {
          expect(mockDataService.getCurrentUser).toHaveBeenCalled();
          done();
        });
      });
    });
  });

  describe('currentUser$ observable', () => {
    it('should emit null initially', (done: DoneFn) => {
      let emissions: (UserInfo | null)[] = [];
      service.currentUser$.subscribe(user => {
        emissions.push(user);
        if (emissions.length === 1) {
          expect(emissions[0]).toBeNull();
          done();
        }
      });
    });

    it('should emit user after getCurrentUser is called', (done: DoneFn) => {
      let emissions: (UserInfo | null)[] = [];
      service.currentUser$.subscribe(user => {
        emissions.push(user);
      });

      service.getCurrentUser().subscribe(() => {
        // Give time for BehaviorSubject to emit
        setTimeout(() => {
          expect(emissions).toContain(mockUserInfo as UserInfo);
          done();
        }, 0);
      });
    });
  });

  describe('loading$ observable', () => {
    it('should emit false initially', (done: DoneFn) => {
      service.loading$.subscribe(loading => {
        expect(loading).toBe(false);
        done();
      });
    });
  });

  describe('loaded$ observable', () => {
    it('should emit false initially', (done: DoneFn) => {
      service.loaded$.subscribe(loaded => {
        expect(loaded).toBe(false);
        done();
      });
    });

    it('should emit true after load', (done: DoneFn) => {
      service.getCurrentUser().subscribe(() => {
        service.loaded$.subscribe(loaded => {
          expect(loaded).toBe(true);
          done();
        });
      });
    });
  });

  describe('concurrent calls', () => {
    it('should only make one API call for concurrent getCurrentUser calls', (done: DoneFn) => {
      let completedCalls = 0;
      const checkComplete = () => {
        completedCalls++;
        if (completedCalls === 3) {
          expect(mockDataService.getCurrentUser).toHaveBeenCalledTimes(1);
          done();
        }
      };

      service.getCurrentUser().subscribe(checkComplete);
      service.getCurrentUser().subscribe(checkComplete);
      service.getCurrentUser().subscribe(checkComplete);
    });
  });

  describe('ngOnDestroy', () => {
    it('should unsubscribe from unauthorized events', () => {
      service.ngOnDestroy();

      // Load the user first
      mockDataService.getCurrentUser.and.returnValue(of(mockUserInfo as UserInfo));

      // Need to create a fresh instance to test this properly
      const freshService = new CurrentUserService(mockDataService);
      freshService.getCurrentUser().subscribe(() => {
        freshService.ngOnDestroy();

        // Emit unauthorized - should not affect the destroyed service
        unauthorizedEmitter.emit(new DataError('Unauthorized', 401, 'Unauthorized'));

        // The service should still have the user since it's destroyed
        // (though in practice you wouldn't use a destroyed service)
        expect(freshService.getUser()).toEqual(mockUserInfo as UserInfo);
      });
    });
  });
});
