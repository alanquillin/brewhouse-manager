import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CurrentUserService } from '../../_services/current-user.service';
import { DataError } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';
import { UserInfo } from '../../models/models';

import * as _ from 'lodash';
import { isNilOrEmpty } from '../../utils/helpers';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  standalone: false,
})
export class HeaderComponent implements OnInit {
  userInfo!: UserInfo | null;

  constructor(
    private currentUserService: CurrentUserService,
    private settingsService: SettingsService,
    private router: Router,
    private _snackBar: MatSnackBar
  ) {}
  @Input() title = '';

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

  logout() {
    this.goto('logout');
  }

  goto(path: string): void {
    window.location.href = `/${path}`;
  }

  get name(): string {
    if (_.isNil(this.userInfo)) {
      return 'UNKNOWN';
    }
    return `${this.userInfo.firstName} ${this.userInfo.lastName}`;
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
