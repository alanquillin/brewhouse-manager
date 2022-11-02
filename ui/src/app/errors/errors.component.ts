import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, OnInit, Inject, AfterViewInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { DataService, DataError } from '../_services/data.service';
import { gsap } from 'gsap'
import { UserInfo } from '../models/models';


import { isNilOrEmpty } from '../utils/helpers';
import * as _ from 'lodash';

@Component({
  selector: 'app-errors',
  templateUrl: './errors.component.html',
  styleUrls: ['./errors.component.scss']
})
export class ErrorsComponent implements OnInit, AfterViewInit {

  errorType: string | undefined;
  userInfo!: UserInfo;
  loading: boolean = false;
  
  isNilOrEmpty = isNilOrEmpty;

  constructor(private dataService: DataService, private router: Router, private route: ActivatedRoute, private _snackBar: MatSnackBar) { }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  ngOnInit() {
    this.loading = true;
    this.errorType = this.route.snapshot.data["error"];

    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        if(this.errorType === 'unauthorized' && isNilOrEmpty(userInfo)){
          return this.goto("login");
        }

        this.userInfo = userInfo;
        this.loading = false;
      },
      error: (err: DataError) => {
        console.log(err)
        if(err.statusCode !== 401) {
          return this.goto("login");
        }
        this.loading = false;
      }
    });
  }

  ngAfterViewInit(): void {
    if(this.errorType === 'notFound') {
      this.animateSpaceman();
    }
  }

  get statusCode(): string {
    if(this.errorType === 'forbidden'){
      return "403"
    }

    if(this.errorType === 'unauthorized'){
      return "401"
    }

    return "<unknown status code>"
  }

  animateSpaceman() {
    gsap.set("svg", { visibility: "visible" });
    gsap.to("#headStripe", {
      y: 0.5,
      rotation: 1,
      yoyo: true,
      repeat: -1,
      ease: "sine.inOut",
      duration: 1
    });
    gsap.to("#spaceman", {
      y: 0.5,
      rotation: 1,
      yoyo: true,
      repeat: -1,
      ease: "sine.inOut",
      duration: 1
    });
    gsap.to("#craterSmall", {
      x: -3,
      yoyo: true,
      repeat: -1,
      duration: 1,
      ease: "sine.inOut"
    });
    gsap.to("#craterBig", {
      x: 3,
      yoyo: true,
      repeat: -1,
      duration: 1,
      ease: "sine.inOut"
    });
    gsap.to("#planet", {
      rotation: -2,
      yoyo: true,
      repeat: -1,
      duration: 1,
      ease: "sine.inOut",
      transformOrigin: "50% 50%"
    });

    gsap.to("#starsBig g", {
      rotation: "random(-30,30)",
      transformOrigin: "50% 50%",
      yoyo: true,
      repeat: -1,
      ease: "sine.inOut"
    });
    gsap.fromTo(
      "#starsSmall g",
      { scale: 0, transformOrigin: "50% 50%" },
      { scale: 1, transformOrigin: "50% 50%", yoyo: true, repeat: -1, stagger: 0.1 }
    );
    gsap.to("#circlesSmall circle", {
      y: -4,
      yoyo: true,
      duration: 1,
      ease: "sine.inOut",
      repeat: -1
    });
    gsap.to("#circlesBig circle", {
      y: -2,
      yoyo: true,
      duration: 1,
      ease: "sine.inOut",
      repeat: -1
    });

    gsap.set("#glassShine", { x: -68 });

    gsap.to("#glassShine", {
      x: 80,
      duration: 2,
      rotation: -30,
      ease: "expo.inOut",
      transformOrigin: "50% 50%",
      repeat: -1,
      repeatDelay: 8,
      delay: 2
    });
  }
  
  goHome(): void {
    this.goto("");
  }

  goto(path: string): void {
    window.location.href = `/${path}`;
  }
}
