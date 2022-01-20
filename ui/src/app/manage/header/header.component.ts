import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, OnInit } from '@angular/core';
import { DataService } from './../../data.service';
import { Router } from '@angular/router';
import { UserInfo, DataError } from '../../models/models';

import * as _ from 'lodash';

@Component({
  selector: 'app-manage-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class ManageHeaderComponent implements OnInit {

  userInfo!: UserInfo;

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) {}

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  ngOnInit() {
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;
      },
      error: (err: DataError) => { 
        this.displayError(err.message);
      }
    });
  }

  logout() {
    window.location.href = '/logout';
  }

  redirectToProfile() {
    window.location.href = '/me';
  }

  redirectToDashboard() {
    window.location.href = '/manage';
  }
  
  get name(): string {
    if(_.isNil(this.userInfo)){
      return "UNKNOWN";
    }
    return `${this.userInfo.firstName} ${this.userInfo.lastName}`;
  }
}
