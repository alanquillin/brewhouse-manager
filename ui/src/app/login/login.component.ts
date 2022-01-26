import { Component, OnInit } from '@angular/core';
import { DataService } from './../data.service';
import { Router } from '@angular/router';
import { FormGroup, Validators, FormControl } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

import { DataError, Settings } from '../models/models'
import { DomSanitizer } from '@angular/platform-browser';
import { MatIconRegistry } from '@angular/material/icon';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  
  loading = false;
  loginFormGroup: FormGroup = new FormGroup({
    email: new FormControl('', [Validators.required]),
    password: new FormControl('', [Validators.required])
  });

  email!: string;
  password!: string;
  processing: boolean = false;
  settings: Settings = new Settings();
  
  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar, private domSanitizer: DomSanitizer, private matIconRegistry: MatIconRegistry) { 
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
    })
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  submit(): void {
    this.processing = true;
    this.dataService.login(this.email, this.password).subscribe({
      next: (data: any) => {

        this.router.navigate(["/manage"]);
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
