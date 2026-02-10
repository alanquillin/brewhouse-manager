import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subscription, of } from 'rxjs';
import { catchError, filter, switchMap, take, tap } from 'rxjs/operators';

import { UserInfo } from '../models/models';
import { DataError, DataService } from './data.service';

/**
 * Service that caches the current user data.
 *
 * Features:
 * - Lazy loads user data on first request (not on app startup)
 * - Returns null if user is not logged in
 * - Provides refresh() method to call after successful login
 * - Provides clear() method to call on logout
 * - Automatically clears cache when any API call receives a 401
 */
@Injectable({
  providedIn: 'root',
})
export class CurrentUserService implements OnDestroy {
  private userSubject = new BehaviorSubject<UserInfo | null>(null);
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private loadedSubject = new BehaviorSubject<boolean>(false);
  private unauthorizedSubscription: Subscription;

  /** Observable of the current user. Emits null if not logged in or not yet loaded. */
  public currentUser$: Observable<UserInfo | null> = this.userSubject.asObservable();

  /** Observable indicating if user data is currently being loaded. */
  public loading$: Observable<boolean> = this.loadingSubject.asObservable();

  /** Observable indicating if user data has been loaded at least once. */
  public loaded$: Observable<boolean> = this.loadedSubject.asObservable();

  constructor(private dataService: DataService) {
    // Subscribe to unauthorized events to clear the cache on 401
    this.unauthorizedSubscription = this.dataService.unauthorized.subscribe(() => {
      this.clear();
    });
  }

  ngOnDestroy(): void {
    this.unauthorizedSubscription.unsubscribe();
  }

  /**
   * Get the current user. Triggers a load from the API if not already loaded.
   * Returns an Observable that emits the UserInfo or null if not logged in.
   */
  getCurrentUser(): Observable<UserInfo | null> {
    if (this.loadedSubject.value) {
      // Already loaded, return cached value
      return of(this.userSubject.value);
    }

    if (this.loadingSubject.value) {
      // Currently loading, wait for it to complete
      return this.loadedSubject.pipe(
        filter(loaded => loaded),
        take(1),
        switchMap(() => of(this.userSubject.value))
      );
    }

    // Not loaded and not loading, trigger a load
    return this.load();
  }

  /**
   * Get the current cached user synchronously.
   * Returns null if not loaded or not logged in.
   */
  getUser(): UserInfo | null {
    return this.userSubject.value;
  }

  /**
   * Check if the user data has been loaded.
   */
  isLoaded(): boolean {
    return this.loadedSubject.value;
  }

  /**
   * Refresh the current user data from the API.
   * Should be called after successful login.
   */
  refresh(): Observable<UserInfo | null> {
    return this.load();
  }

  /**
   * Clear the cached user data.
   * Should be called on logout or when a 401 is received.
   */
  clear(): void {
    this.userSubject.next(null);
    this.loadedSubject.next(false);
    this.loadingSubject.next(false);
  }

  /**
   * Load user data from the API.
   */
  private load(): Observable<UserInfo | null> {
    this.loadingSubject.next(true);

    return this.dataService.getCurrentUser(true).pipe(
      tap((userInfo: UserInfo) => {
        this.userSubject.next(userInfo);
        this.loadedSubject.next(true);
        this.loadingSubject.next(false);
      }),
      catchError((err: DataError) => {
        this.loadingSubject.next(false);
        this.loadedSubject.next(true);

        if (err.statusCode === 401) {
          // User is not logged in, return null
          this.userSubject.next(null);
          return of(null);
        }

        // Re-throw other errors
        throw err;
      })
    );
  }
}
