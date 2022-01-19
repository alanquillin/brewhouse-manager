import { Component, OnInit } from '@angular/core';
import { DataService } from './../data.service';
import { Router } from '@angular/router';
import { FormGroup, Validators, FormControl } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

import { DataError } from '../models/models'
import { DomSanitizer } from '@angular/platform-browser';
import { MatIconRegistry } from '@angular/material/icon';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  
  loginFormGroup: FormGroup = new FormGroup({
    email: new FormControl('', [Validators.required]),
    password: new FormControl('', [Validators.required])
  });

  email!: string;
  password!: string;
  processing: boolean = false;
  
  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar, private domSanitizer: DomSanitizer, private matIconRegistry: MatIconRegistry) { 
    this.matIconRegistry.addSvgIcon(
      "logo",
      this.domSanitizer.bypassSecurityTrustResourceUrl("https://raw.githubusercontent.com/fireflysemantics/logo/master/Google.svg"));
  }

  ngOnInit(): void {}

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
        if (err.statusCode === 401) {
          this.displayError("Invalid username or password")
        } else {
          this.displayError("An unknown error occurred trying to login.")
        }
      },
      complete: () => {
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
