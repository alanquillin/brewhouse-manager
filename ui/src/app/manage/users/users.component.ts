import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { UntypedFormControl, AbstractControl, Validators, UntypedFormGroup } from '@angular/forms';
import { Validation } from '../../utils/form-validators';

import { Location, UserInfo } from '../../models/models';

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
  displayedColumns: string[] = ['email', 'firstName', 'lastName', "admin", "locationCount", "isPasswordEnabled", "profilePic", "actions"];
  processing = false;
  adding = false;
  editing = false;
  changePassword = false;
  modifyUser: UserInfo = new UserInfo();
  hidePassword = true;
  locations: Location[] = [];
  selectedLocations: any = {};
  newPassword = "";
  confirmNewPassword = "";

  isNilOrEmpty = isNilOrEmpty;
  _ = _;

  modifyFormGroup: UntypedFormGroup = new UntypedFormGroup({
    email: new UntypedFormControl('', [Validators.required, Validators.email]),
    firstName: new UntypedFormControl(''),
    lastName: new UntypedFormControl(''),
    profilePic: new UntypedFormControl(''),
    password: new UntypedFormControl(''),
    admin: new UntypedFormControl('')
  });

  changePasswordFormGroup: UntypedFormGroup = new UntypedFormGroup({
    password: new UntypedFormControl('', [Validators.required, Validators.pattern('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&]).{8,}')]),
    confirmPassword: new UntypedFormControl('', [Validators.required])
  }, { validators: [Validation.match('password', 'confirmPassword')] });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = [];
        for(let l of _.sortBy(locations, [(l:Location) => {return l.description}])) {
          this.selectedLocations[l.id] = false;
          this.locations.push(new Location(l));
        }
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
        });
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
    });
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
    this.resetSelectedLocations();
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
        this.saveLocations(new UserInfo(user), () => {
          this.refresh(() => {this.processing = false;}, () => {this.adding = false;});
        });
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
    this.resetSelectedLocations();
    if(user.locations) {
      for(let l of user.locations) {
        this.selectedLocations[l.id] = true;
      }
    }
  }

  save(): void {
    if(!this.modifyUser.hasChanges) {
      return this.saveLocations(this.modifyUser, () => {
        this.modifyUser.disableEditing();
        this.refresh(()=> {this.processing = false;}, () => {
          this.editing = false;
        })
      });
    }

    this.processing = true;
    this.dataService.updateUser(this.modifyUser.id, this.modifyUser.changes).subscribe({
      next: (user: UserInfo) => {
        return this.saveLocations(this.modifyUser, () => {
          this.modifyUser.disableEditing();
          this.refresh(()=> {this.processing = false;}, () => {
            this.editing = false;
          });
        });
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  saveLocations(user: UserInfo, next:Function): void {
    if(!this.selectedLocationChanges()) {
      next();
      return;
    }
    this.processing = true;
    let locations: string[] = [];
    _.each(this.selectedLocations, (value, key) => {
      if(value === true) {
        locations.push(key)
      }
    }); 

    this.dataService.updateUserLocations(user.id, {"locationIds": locations}).subscribe({
      next: (res: any) => {
        next();
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
          this.processing = false;
          this.loading = true;
          this.refresh(()=>{ this.loading = false; });
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

  reRunValidation(): void {
    _.forEach(this.modifyForm, (ctrl) => {
      ctrl.updateValueAndValidity();
    });
  }

  changeLocationsSelection(selected: boolean, location: Location) : void {
    this.selectedLocations[location.id] = selected;
  }

  selectedLocationChanges(): boolean {
    let expected: string[] = [];
    if(this.modifyUser.locations) {
      for(let l of this.modifyUser.locations) {
        expected.push(l.id)
      }
    }
    expected.sort();

    let actual: string[] = [];
    _.each(this.selectedLocations, (value, key) => {
      if(value === true) {
        actual.push(key);
      }
    });
    actual.sort();

    return !_.isEqual(expected, actual);
  }

  resetSelectedLocations(): void {
    for(let l of this.locations) {
      this.selectedLocations[l.id] = false;
    }
  }

  get changes(): boolean {
    return this.modifyUser.hasChanges || this.selectedLocationChanges();
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
    this.dataService.updateUser(this.modifyUser.id, {password: this.newPassword}).subscribe({
      next: (data: UserInfo) => {
        this.edit(new UserInfo(data));
        this.changePassword = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  disablePassword(): void {
    if(confirm("Are you sure you want to disable the user's password?  Doing so will prevent them from logging in with username and password.  You will need to log in via Google instead.")) {
      this.processing = true;
      this.dataService.updateUser(this.modifyUser.id, {password: null}).subscribe({
        next: (data: UserInfo) => {
          this.edit(new UserInfo(data));
          this.processing = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      });
    }
  }

  get changePasswordForm(): { [key: string]: AbstractControl } {
    return this.changePasswordFormGroup.controls;
  }
}
