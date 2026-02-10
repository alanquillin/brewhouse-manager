import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { Settings } from '../models/models';
import { DataService } from './data.service';
import { SettingsService } from './settings.service';

describe('SettingsService', () => {
  let service: SettingsService;
  let mockDataService: jasmine.SpyObj<DataService>;

  const mockSettingsData: any = {
    googleSSOEnabled: true,
    taps: { refresh: { baseSec: 300, variable: 150 } },
    beverages: { supportedTypes: ['beer', 'cider'] },
    dashboard: { refreshSec: 30 },
    plaato_keg_devices: { enabled: true, host: 'localhost', port: 8080 },
  };

  beforeEach(() => {
    mockDataService = jasmine.createSpyObj('DataService', ['getSettings']);
    mockDataService.getSettings.and.returnValue(of(mockSettingsData) as any);

    TestBed.configureTestingModule({
      providers: [SettingsService, { provide: DataService, useValue: mockDataService }],
    });
    service = TestBed.inject(SettingsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('settings$', () => {
    it('should be an observable', () => {
      expect(service.settings$).toBeTruthy();
      expect(typeof service.settings$.subscribe).toBe('function');
    });

    it('should emit default Settings initially', (done: DoneFn) => {
      service.settings$.subscribe(settings => {
        expect(settings).toBeInstanceOf(Settings);
        done();
      });
    });
  });

  describe('loadSettings', () => {
    it('should call dataService.getSettings', async () => {
      await service.loadSettings();
      expect(mockDataService.getSettings).toHaveBeenCalled();
    });

    it('should return Settings instance', async () => {
      const result = await service.loadSettings();
      expect(result).toBeInstanceOf(Settings);
    });

    it('should update settings$ observable', async () => {
      await service.loadSettings();

      service.settings$.subscribe(settings => {
        expect(settings.googleSSOEnabled).toBe(true);
      });
    });

    it('should map response data to Settings', async () => {
      const result = await service.loadSettings();
      expect(result.googleSSOEnabled).toBe(true);
    });

    it('should handle API errors', async () => {
      mockDataService.getSettings.and.returnValue(throwError(() => new Error('API Error')));

      await expectAsync(service.loadSettings()).toBeRejectedWithError('API Error');
    });
  });

  describe('getSettings', () => {
    it('should return current settings snapshot', () => {
      const settings = service.getSettings();
      expect(settings).toBeInstanceOf(Settings);
    });

    it('should return default settings before loadSettings is called', () => {
      const settings = service.getSettings();
      expect(settings.googleSSOEnabled).toBe(false);
    });

    it('should return loaded settings after loadSettings is called', async () => {
      await service.loadSettings();
      const settings = service.getSettings();
      expect(settings.googleSSOEnabled).toBe(true);
    });
  });

  describe('getSetting', () => {
    beforeEach(async () => {
      await service.loadSettings();
    });

    it('should get top-level setting', () => {
      const value = service.getSetting<boolean>('googleSSOEnabled');
      expect(value).toBe(true);
    });

    it('should get nested setting with dot notation', () => {
      const value = service.getSetting<number>('taps.refresh.baseSec');
      expect(value).toBe(300);
    });

    it('should get deeply nested setting', () => {
      const value = service.getSetting<string>('plaato_keg_devices.host');
      expect(value).toBe('localhost');
    });

    it('should return undefined for non-existent path', () => {
      const value = service.getSetting<string>('non.existent.path');
      expect(value).toBeUndefined();
    });

    it('should return undefined for partial non-existent path', () => {
      const value = service.getSetting<string>('taps.nonExistent');
      expect(value).toBeUndefined();
    });

    it('should handle empty path', () => {
      const value = service.getSetting<any>('');
      expect(value).toBeUndefined();
    });

    it('should return object for nested path', () => {
      const value = service.getSetting<object>('taps.refresh');
      expect(value).toEqual({ baseSec: 300, variable: 150 });
    });
  });

  describe('refreshSettings', () => {
    it('should call dataService.getSettings', (done: DoneFn) => {
      service.refreshSettings().subscribe(() => {
        expect(mockDataService.getSettings).toHaveBeenCalled();
        done();
      });
    });

    it('should return Settings observable', (done: DoneFn) => {
      service.refreshSettings().subscribe(settings => {
        expect(settings).toBeInstanceOf(Settings);
        done();
      });
    });

    it('should update settings$ observable', (done: DoneFn) => {
      const updatedData: any = { ...mockSettingsData, googleSSOEnabled: false };
      mockDataService.getSettings.and.returnValue(of(updatedData) as any);

      service.refreshSettings().subscribe(() => {
        service.settings$.subscribe(settings => {
          expect(settings.googleSSOEnabled).toBe(false);
          done();
        });
      });
    });

    it('should propagate errors', (done: DoneFn) => {
      mockDataService.getSettings.and.returnValue(throwError(() => new Error('Refresh failed')));

      service.refreshSettings().subscribe({
        error: err => {
          expect(err.message).toBe('Refresh failed');
          done();
        },
      });
    });
  });

  describe('getSetting edge cases', () => {
    it('should handle null values in path', async () => {
      const dataWithNull: any = { ...mockSettingsData, nullValue: null };
      mockDataService.getSettings.and.returnValue(of(dataWithNull) as any);
      await service.loadSettings();

      const value = service.getSetting<any>('nullValue.nested');
      expect(value).toBeUndefined();
    });

    it('should handle array values', async () => {
      const dataWithArray: any = { ...mockSettingsData, items: ['a', 'b', 'c'] };
      mockDataService.getSettings.and.returnValue(of(dataWithArray) as any);
      await service.loadSettings();

      const value = service.getSetting<string[]>('items');
      expect(value).toEqual(['a', 'b', 'c']);
    });

    it('should handle numeric values', async () => {
      await service.loadSettings();

      const loadedValue = service.getSetting<number>('dashboard.refreshSec');
      expect(loadedValue).toBe(30);
    });
  });
});
