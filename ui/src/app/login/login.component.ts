import { Component, OnInit } from '@angular/core';
import { UntypedFormControl, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { DataError, DataService } from '../_services/data.service';
import { SettingsService } from '../_services/settings.service';

import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer } from '@angular/platform-browser';
import { isNilOrEmpty } from '../utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  standalone: false,
})
export class LoginComponent implements OnInit {
  loading = false;
  loginFormGroup: UntypedFormGroup = new UntypedFormGroup({
    email: new UntypedFormControl('', [Validators.required]),
    password: new UntypedFormControl('', [Validators.required]),
  });

  email!: string;
  password!: string;
  processing = false;

  constructor(
    private dataService: DataService,
    private settingsService: SettingsService,
    private router: Router,
    private route: ActivatedRoute,
    private _snackBar: MatSnackBar,
    private domSanitizer: DomSanitizer,
    private matIconRegistry: MatIconRegistry
  ) {
    this.matIconRegistry.addSvgIcon(
      'logo',
      this.domSanitizer.bypassSecurityTrustResourceUrl(
        'https://raw.githubusercontent.com/fireflysemantics/logo/master/Google.svg'
      )
    );
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const err = _.get(params, 'error');
      if (!isNilOrEmpty(err)) {
        this.displayError(err);
      }
    });
  }

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  submit(): void {
    this.processing = true;
    this.dataService.login(this.email, this.password).subscribe({
      next: (data: any) => {
        window.location.href = '/manage';
      },
      error: (err: DataError) => {
        if (err.statusCode === 400) {
          this.displayError(err.message);
        } else if (err.statusCode === 401) {
          this.displayError('Invalid username or password');
        } else {
          this.displayError('An unknown error occurred trying to login.');
        }
        this.processing = false;
      },
    });
  }

  loginWithGoogle() {
    location.href = '/login/google';
  }

  get loginForm() {
    return this.loginFormGroup.controls;
  }

  get googleSSOEnabled(): boolean {
    return this.settingsService.getSetting<boolean>('googleSSOEnabled') || false;
  }
}
