import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, OnInit } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Router } from '@angular/router';
import { AbstractControl, UntypedFormGroup, Validators, UntypedFormControl } from '@angular/forms';

import { UserInfo } from '../models/models';
import { Validation } from '../utils/form-validators';
import { isNilOrEmpty } from '../utils/helpers';

import * as _ from 'lodash';


@Component({
    selector: 'app-profile',
    templateUrl: './profile.component.html',
    styleUrls: ['./profile.component.scss'],
    standalone: false
})
export class ProfileComponent implements OnInit {
  
  userInfo: UserInfo = new UserInfo();
  editing = false;
  changePassword = false;
  processing = false;

  isNilOrEmpty = isNilOrEmpty;
  _ = _;

  newPassword: string= "";
  confirmNewPassword: string = "";

  editFormGroup: UntypedFormGroup = new UntypedFormGroup({
    email: new UntypedFormControl('', [Validators.required, Validators.email]),
    firstName: new UntypedFormControl('', [Validators.required]),
    lastName: new UntypedFormControl('', [Validators.required]),
    profilePic: new UntypedFormControl('', [])
  });

  changePasswordFormGroup: UntypedFormGroup = new UntypedFormGroup({
    password: new UntypedFormControl('', [Validators.required, Validators.pattern('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&]).{8,}')]),
    confirmPassword: new UntypedFormControl('', [Validators.required])
  }, { validators: [Validation.match('password', 'confirmPassword')] });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) {}

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.processing = true;
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = new UserInfo(userInfo);
        this.processing = false;
        if(!_.isNil(next)){
          next();
        }
        if(!_.isNil(always)){
          always();
        }
      }, 
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
        if(!_.isNil(error)){
          error();
        }
        if(!_.isNil(always)){
          always();
        }
      }
    })
  }

  ngOnInit() {
    this.refresh();
  }

  cancelEditing(): void {
    this.editing = false;
    this.userInfo.disableEditing();
  }

  startEditing(): void {
    this.userInfo.enableEditing();
    this.editing = true;
  }

  save(): void {
    if (this.editFormGroup.invalid) {
      return;
    }
    
    this.processing = true;
    
    this.dataService.updateUser(this.userInfo.id, this.userInfo.changes).subscribe({
      next: (data: UserInfo) => {
        this.userInfo = new UserInfo(data);
        this.editing = false;
        this.processing = false;
        this.userInfo.disableEditing();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  cancelChangePassword(): void {
    this.changePassword = false;
  }

  startChangePassword(): void {
    this.newPassword = "";
    this.confirmNewPassword = "";
    this.changePassword = true;
  }

  savePassword(): void {
    if (this.changePasswordFormGroup.invalid) {
      return;
    }
    
    this.processing = true;
    this.dataService.updateUser(this.userInfo.id, {password: this.newPassword}).subscribe({
      next: (data: UserInfo) => {
        this.userInfo = new UserInfo(data);
        this.changePassword = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  disablePassword(): void {
    if(confirm("Are you sure you want to disable your password?  Doing so will prevent you from logging in with username and password.  You will need to log in via Google instead.")) {
      this.processing = true;
      this.dataService.updateUser(this.userInfo.id, {password: null}).subscribe({
        next: (data: UserInfo) => {
          this.userInfo = new UserInfo(data);
          this.editing = false;
          this.processing = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      });
    }
  }

  _generateAPIKey(user: UserInfo): void {
    this.processing = true;
    this.dataService.generateUserAPIKey(user.id).subscribe({
      next: (resp: string) => {
        user.apiKey = resp;
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  generateAPIKey(): void {
    let user = this.userInfo;
    if(!isNilOrEmpty(user.apiKey)) {
      if(confirm(`Are you sure you want to regenerate your API key?  The previous key will be invalidated.`)) {
        this._generateAPIKey(user);
      }
    } else {
      this._generateAPIKey(user);
    }
  }

  deleteAPIKey(): void {
    this.processing = true;
    if(confirm(`Are you sure you want to delete your API key?`)) {
      this.dataService.deleteUserAPIKey(this.userInfo.id).subscribe({
        next: (resp: string) => {
          this.userInfo.apiKey = "";
          this.processing = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      });
    }
  }

  get name(): string {
    if(_.isNil(this.userInfo)){
      return "UNKNOWN";
    }
    return `${this.userInfo.firstName} ${this.userInfo.lastName}`;
  }

  get editForm(): { [key: string]: AbstractControl } {
    return this.editFormGroup.controls;
  }

  get changePasswordForm(): { [key: string]: AbstractControl } {
    return this.changePasswordFormGroup.controls;
  }
}
