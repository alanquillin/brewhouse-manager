import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, Input, OnInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { UserInfo } from '../../models/models';

import * as _ from 'lodash';
import { isNilOrEmpty } from '../../utils/helpers';

@Component({
    selector: 'app-header',
    templateUrl: './header.component.html',
    styleUrls: ['./header.component.scss'],
    standalone: false
})
export class HeaderComponent implements OnInit {

  userInfo!: UserInfo;

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) {}
  @Input() title: string = "";

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  ngOnInit() {
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;
      },
      error: (err: DataError) => {
        if(err.statusCode !== 401) {
          this.displayError(err.message);
        }
      }
    });
  }

  logout() {
    this.goto('logout');
  }

  goto(path: string): void {
    window.location.href = `/${path}`;
  }
  
  get name(): string {
    if(_.isNil(this.userInfo)){
      return "UNKNOWN";
    }
    return `${this.userInfo.firstName} ${this.userInfo.lastName}`;
  }

  get admin(): boolean {
    if(isNilOrEmpty(this.userInfo)) {
      return false
    }

    return this.userInfo.admin;
  }
}
