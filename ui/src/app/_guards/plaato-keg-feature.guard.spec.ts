import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';

import { SettingsService } from '../_services/settings.service';
import { PlaatoKegFeatureGuard } from './plaato-keg-feature.guard';

describe('PlaatoKegFeatureGuard', () => {
  let guard: PlaatoKegFeatureGuard;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockUrlTree: UrlTree;

  beforeEach(() => {
    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting']);
    mockUrlTree = { toString: () => '/404' } as UrlTree;
    mockRouter = jasmine.createSpyObj('Router', ['parseUrl']);
    mockRouter.parseUrl.and.returnValue(mockUrlTree);

    TestBed.configureTestingModule({
      providers: [
        PlaatoKegFeatureGuard,
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: Router, useValue: mockRouter },
      ],
    });

    guard = TestBed.inject(PlaatoKegFeatureGuard);
  });

  it('should be created', () => {
    expect(guard).toBeTruthy();
  });

  describe('canActivate', () => {
    it('should return true when plaato_keg_devices.enabled is true', () => {
      mockSettingsService.getSetting.and.returnValue(true);

      const result = guard.canActivate();

      expect(result).toBe(true);
      expect(mockSettingsService.getSetting).toHaveBeenCalledWith('plaato_keg_devices.enabled');
    });

    it('should return UrlTree to /404 when plaato_keg_devices.enabled is false', () => {
      mockSettingsService.getSetting.and.returnValue(false);

      const result = guard.canActivate();

      expect(result).toBe(mockUrlTree);
      expect(mockRouter.parseUrl).toHaveBeenCalledWith('/404');
    });

    it('should return UrlTree to /404 when plaato_keg_devices.enabled is undefined', () => {
      mockSettingsService.getSetting.and.returnValue(undefined);

      const result = guard.canActivate();

      expect(result).toBe(mockUrlTree);
      expect(mockRouter.parseUrl).toHaveBeenCalledWith('/404');
    });

    it('should return UrlTree to /404 when plaato_keg_devices.enabled is null', () => {
      mockSettingsService.getSetting.and.returnValue(null);

      const result = guard.canActivate();

      expect(result).toBe(mockUrlTree);
      expect(mockRouter.parseUrl).toHaveBeenCalledWith('/404');
    });

    it('should check the correct setting path', () => {
      mockSettingsService.getSetting.and.returnValue(true);

      guard.canActivate();

      expect(mockSettingsService.getSetting).toHaveBeenCalledWith('plaato_keg_devices.enabled');
    });
  });

  describe('feature toggle behavior', () => {
    it('should allow access when feature is enabled', () => {
      mockSettingsService.getSetting.and.returnValue(true);

      const result = guard.canActivate();

      expect(result).toBe(true);
    });

    it('should redirect to 404 when feature is disabled', () => {
      mockSettingsService.getSetting.and.returnValue(false);

      const result = guard.canActivate();

      expect(result).toEqual(mockUrlTree);
    });

    it('should handle truthy non-boolean values', () => {
      mockSettingsService.getSetting.and.returnValue('yes' as unknown as boolean);

      const result = guard.canActivate();

      // String 'yes' is truthy, so should return true
      expect(result).toBe(true);
    });

    it('should handle empty string as falsy', () => {
      mockSettingsService.getSetting.and.returnValue('' as unknown as boolean);

      const result = guard.canActivate();

      // Empty string is falsy, so should redirect
      expect(result).toBe(mockUrlTree);
    });
  });
});
