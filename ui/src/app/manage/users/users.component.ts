import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { FormControl, AbstractControl, Validators, FormGroup } from '@angular/forms';

import { UserInfo } from '../../models/models';

import * as _ from 'lodash';
import { isNilOrEmpty } from 'src/app/utils/helpers';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})
export class ManageUsersComponent implements OnInit {
  
  loading = false;
  me: UserInfo = new UserInfo();
  users: UserInfo[] = [];
  filteredUsers: UserInfo[] = [];
  displayedColumns: string[] = ['email', 'firstName', 'lastName', 'profilePic', 'actions'];
  processing = false;
  adding = false;
  editing = false;
  modifyUser: UserInfo = new UserInfo();
  hidePassword = true;

  _ = _;

  modifyFormGroup: FormGroup = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    firstName: new FormControl(''),
    lastName: new FormControl(''),
    profilePic: new FormControl(''),
    password: new FormControl('')
  });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getUsers().subscribe({
      next: (users: UserInfo[]) => {
        this.users = [];
        _.forEach(users, (user) => {
          var _user = new UserInfo()
          Object.assign(_user, user);
          this.users.push(_user)
        })
        this.filter();
      }, 
      error: (err: DataError) => {
        this.displayError(err.message);
        if(!_.isNil(error)){
          error();
        }
        if(!_.isNil(always)){
          always();
        }
      },
      complete: () => {
        if(!_.isNil(next)){
          next();
        }
        if(!_.isNil(always)){
          always();
        }
      }
    })
  }

  ngOnInit(): void {
    this.loading = true;
    this.dataService.getCurrentUser().subscribe({
      next: (me: UserInfo) => {
        this.me = me;
        this.refresh(undefined, ()=> {
          this.loading = false;
        })
      },
      error: (err: DataError) => {
        this.displayError(err.message);
      }
    })
  }

  add(): void {
    this.modifyFormGroup.reset();
    this.modifyUser = new UserInfo();
    this.adding = true;
  }

  create(): void {
    var data: any = {
      email: this.modifyUser.editValues.email,
    }
    const keys = ["firstName", "lastName", "profilePic"];
    _.forEach(keys, (k) => {
      const val = _.get(this.modifyUser.editValues, k);
      if (!isNilOrEmpty(val)) {
        data[k] = val;
      }
    })
    const password = this.modifyForm["password"].value;
    if (!isNilOrEmpty(password)) {
      data["password"] = password;
    }

    this.processing = true;
    this.dataService.createUser(data).subscribe({
      next: (user: UserInfo) => {
        this.refresh(() => {this.processing = false;}, () => {this.adding = false;});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  cancelAdd(): void {
    this.adding = false;
  }

  edit(user: UserInfo): void {
    user.enableEditing();
    this.modifyUser = user;
    this.editing = true;
    this.modifyFormGroup.reset();
  }

  save(): void {
    this.processing = true;
    this.dataService.updateUser(this.modifyUser.id, this.modifyUser.changes).subscribe({
      next: (user: UserInfo) => {
        this.modifyUser.disableEditing();
        this.refresh(()=> {this.processing = false;}, () => {
          this.editing = false;
        })
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  cancelEdit(): void {
    this.modifyUser.disableEditing();
    this.editing = false;
  }

  delete(user: UserInfo): void {
    if(confirm(`Are you sure you want to delete user '${user.email}'?`)) {
      this.processing = true;
      this.dataService.deleteUser(user.id).subscribe({
        next: (resp: any) => {
          this.refresh(()=>{ this.processing = false; });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
    }
  }

  filter(sort?: Sort) {
    var sortBy:string = "description";
    var asc: boolean = true;

    if(!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    var filteredData: UserInfo[] = this.users;
    filteredData = _.sortBy(filteredData, [(d: UserInfo) => { return _.get(d, sortBy)}]);
    if(!asc){
      _.reverse(filteredData);
    }
    this.filteredUsers = filteredData;
  }

  addMissingMeta() {
    switch(this.modifyUser.editValues.userType) {
      case "plaato-keg":
        if(!_.has(this.modifyUser.editValues.meta, "authToken")){
          _.set(this.modifyUser.editValues, 'meta.authToken', '');
        }
        break
    }
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  }  
}
