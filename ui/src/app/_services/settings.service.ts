import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, firstValueFrom } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { Settings } from '../models/models';
import { DataService } from './data.service';

@Injectable({
  providedIn: 'root',
})
export class SettingsService {
  private settingsSubject = new BehaviorSubject<Settings>(new Settings());

  public settings$: Observable<Settings> = this.settingsSubject.asObservable();

  constructor(private dataService: DataService) {}

  /**
   * Load settings from the API
   * This should be called during app initialization
   */
  loadSettings(): Promise<Settings> {
    return firstValueFrom(
      this.dataService.getSettings().pipe(
        map(data => new Settings(data)),
        tap(settings => {
          this.settingsSubject.next(settings);
        })
      )
    );
  }

  /**
   * Get current settings snapshot
   */
  getSettings(): Settings {
    return this.settingsSubject.value;
  }

  /**
   * Get a specific setting value by path
   * Example: getSetting('plaato_keg_device_config.host')
   */
  getSetting<T>(path: string): T | undefined {
    const keys = path.split('.');
    let value: any = this.settingsSubject.value;

    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return undefined;
      }
    }

    return value as T;
  }

  /**
   * Refresh settings from the API
   */
  refreshSettings(): Observable<Settings> {
    return this.dataService.getSettings().pipe(
      map(data => new Settings(data)),
      tap(settings => {
        this.settingsSubject.next(settings);
      })
    );
  }
}
