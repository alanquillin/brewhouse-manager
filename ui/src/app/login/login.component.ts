import { Component, OnInit } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Router, ActivatedRoute } from '@angular/router';
import { UntypedFormGroup, Validators, UntypedFormControl } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Settings } from '../models/models'
import { DomSanitizer } from '@angular/platform-browser';
import { MatIconRegistry } from '@angular/material/icon';
import { isNilOrEmpty } from '../utils/helpers';

import * as _ from 'lodash';

@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss'],
    standalone: false
})
export class LoginComponent implements OnInit {
  
  loading = false;
  loginFormGroup: UntypedFormGroup = new UntypedFormGroup({
    email: new UntypedFormControl('', [Validators.required]),
    password: new UntypedFormControl('', [Validators.required])
  });

  email!: string;
  password!: string;
  processing: boolean = false;
  settings: Settings = new Settings();
  
  constructor(private dataService: DataService, private router: Router, private route: ActivatedRoute, private _snackBar: MatSnackBar, private domSanitizer: DomSanitizer, private matIconRegistry: MatIconRegistry) { 
    this.matIconRegistry.addSvgIcon(
      "logo",
      this.domSanitizer.bypassSecurityTrustResourceUrl("https://raw.githubusercontent.com/fireflysemantics/logo/master/Google.svg"));
  }

  ngOnInit(): void {
    this.loading = true;
    this.dataService.getSettings().subscribe({
      next: (settings: Settings) => {
        this.settings = settings;
        this.loading = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.loading = false;
      }
    });
    this.route.queryParams.subscribe(params => {
      const err = _.get(params, "error");
      if(!isNilOrEmpty(err)) {
        this.displayError(err);
      }
    });
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  submit(): void {
    this.processing = true;
    this.dataService.login(this.email, this.password).subscribe({
      next: (data: any) => {
        window.location.href = "/manage";
      },
      error: (err: DataError) => {
        if (err.statusCode === 400) {
          this.displayError(err.message)
        } else if (err.statusCode === 401) {
          this.displayError("Invalid username or password")
        } else {
          this.displayError("An unknown error occurred trying to login.")
        }
        this.processing = false;
      }
    });
  }

  loginWithGoogle() {
    location.href = "/login/google";
  }

  get loginForm() {
    return this.loginFormGroup.controls;
  }
}
