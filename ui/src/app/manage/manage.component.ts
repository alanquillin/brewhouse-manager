import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CurrentUserService } from '../_services/current-user.service';
import { DataError } from '../_services/data.service';
import { SettingsService } from '../_services/settings.service';
import { UserInfo } from '../models/models';

import { isNilOrEmpty } from '../utils/helpers';

@Component({
  selector: 'manage',
  templateUrl: './manage.component.html',
  styleUrls: ['./manage.component.scss'],
  standalone: false,
})
export class ManageComponent implements OnInit {
  title = 'Manage Brewhouse';

  isLoading = false;

  userInfo!: UserInfo | null;

  constructor(
    private currentUserService: CurrentUserService,
    private settingsService: SettingsService,
    private router: Router,
    private _snackBar: MatSnackBar
  ) {}

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  ngOnInit() {
    this.currentUserService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo | null) => {
        this.userInfo = userInfo;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
      },
    });
  }

  goto(path: string): void {
    window.location.href = `/${path}`;
  }

  get admin(): boolean {
    if (isNilOrEmpty(this.userInfo)) {
      return false;
    }

    return this.userInfo!.admin;
  }

  get plaatoKegEnabled(): boolean {
    return this.settingsService.getSetting<boolean>('plaato_keg_devices.enabled') || false;
  }
}
