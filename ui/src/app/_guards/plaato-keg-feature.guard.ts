import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';
import { SettingsService } from '../_services/settings.service';

@Injectable({
  providedIn: 'root',
})
export class PlaatoKegFeatureGuard implements CanActivate {
  constructor(
    private settingsService: SettingsService,
    private router: Router
  ) {}

  canActivate(): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    const isEnabled = this.settingsService.getSetting<boolean>('plaato_keg_devices.enabled');

    if (isEnabled) {
      return true;
    }

    // Redirect to 404 page if feature is disabled
    return this.router.parseUrl('/404');
  }
}
