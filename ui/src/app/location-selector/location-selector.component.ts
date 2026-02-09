import { Component, OnInit } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { DataError, DataService } from '../_services/data.service';

import { Location } from './../models/models';

import * as _ from 'lodash';

@Component({
  selector: 'location-selector',
  templateUrl: './location-selector.component.html',
  styleUrls: ['./location-selector.component.scss'],
  standalone: false,
})
export class LocationSelectorComponent implements OnInit {
  title = 'Location Selector';

  loading = false;
  locations: Location[] = [];

  constructor(
    private dataService: DataService,
    private router: Router,
    private _snackBar: MatSnackBar
  ) {}

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  refresh() {
    this.loading = true;
    this.dataService.getDashboardLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = _.sortBy(locations, l => {
          return l.description;
        });
        if (locations.length == 0) {
          // redirect via the window to make sure the backend code is hit in case the user is not logged in yet
          window.location.href = '/manage';
        } else if (locations.length == 1) {
          this.selectLocation(locations[0]);
        } else {
          this.loading = false;
        }
      },
      error: (err: DataError) => {
        this.displayError(err.message);
      },
    });
  }

  ngOnInit() {
    this.refresh();
  }

  selectLocation(location: Location) {
    this.router.navigate(['view/' + location.name]);
  }
}
