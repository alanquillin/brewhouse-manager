import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, OnInit } from '@angular/core';
import { DataService } from './../data.service';
import { Router } from '@angular/router';
import { AbstractControl, FormGroup, Validators, FormControl } from '@angular/forms';

import { DataError, UserInfo } from '../models/models';
import { Validation } from '../form-validators';

import * as _ from 'lodash';


@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  
  userInfo!: UserInfo;
  editUserInfo!: UserInfo;
  editing = false;
  changePassword = false;
  processing = false;
  _ = _;

  newPassword: string= "";
  confirmNewPassword: string = "";

  editFormGroup: FormGroup = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    firstName: new FormControl('', [Validators.required]),
    lastName: new FormControl('', [Validators.required]),
    profilePic: new FormControl('', [Validators.required])
  });

  changePasswordFormGroup: FormGroup = new FormGroup({
    password: new FormControl('', [Validators.required, Validators.pattern('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&]).{8,}')]),
    confirmPassword: new FormControl('', [Validators.required])
  }, { validators: [Validation.match('password', 'confirmPassword')] });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) {}

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  ngOnInit() {
    console.log(this.userInfo)
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;
        console.log(this.userInfo);
      },
      error: (err: DataError) => { 
        this.displayError(err.message);
      }
    });
  }

  cancelEditing(): void {
    this.editing = false;
  }

  startEditing(): void {
    this.editing = true;
    this.editUserInfo = { ...this.userInfo }
  }

  getChanges() {
    var updateData: any = {}

    if(this.editUserInfo.firstName !== this.userInfo.firstName) {
      updateData.firstName = this.editUserInfo.firstName;
    }
    if(this.editUserInfo.lastName !== this.userInfo.lastName) {
      updateData.lastName = this.editUserInfo.lastName;
    }
    if(this.editUserInfo.profilePic !== this.userInfo.profilePic) {
      updateData.profilePic = this.editUserInfo.profilePic;
    }
    if(this.editUserInfo.email !== this.userInfo.email) {
      updateData.email = this.editUserInfo.email;
    }

    return updateData;
  }

  save(): void {
    if (this.editFormGroup.invalid) {
      return;
    }

    var updateData = this.getChanges();

    if(_.isEmpty(updateData)) {
      console.log("nothing to update!")
      this.editing = false;
      return;
    }
    
    this.processing = true;
    
    this.dataService.updateAdmin(this.userInfo.id, updateData).subscribe({
      next: (data: UserInfo) => {
        this.userInfo = data;
        this.editing = false;
        this.processing = false;
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
    this.dataService.updateAdmin(this.userInfo.id, {password: this.newPassword}).subscribe({
      next: (data: UserInfo) => {
        this.userInfo = data;
        this.changePassword = false;
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  disablePassword(): void {
    if(confirm("Are you sure you want to disable your password?  Doing so will prevent you from logging in with username and password.  You will need to log in via Google instead.")) {
      this.processing = true;
      this.dataService.updateAdmin(this.userInfo.id, {password: null}).subscribe({
        next: (data: UserInfo) => {
          this.userInfo = data;
          this.editing = false;
          this.processing = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
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
