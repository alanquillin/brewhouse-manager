import { Component, OnInit } from '@angular/core';
import { DataService, DataError } from './../data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Location } from './../models/models';

@Component({
  selector: 'location-selector',
  templateUrl: './location-selector.component.html',
  styleUrls: ['./location-selector.component.scss']
})
export class LocationSelectorComponent implements OnInit {
  title = 'Location Selector';

  loading = false;
  locations: Location[] = [];

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) {}

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh() {
    this.loading = true;
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = locations
        if (locations.length == 0) {
          // redirect via the window to make sure the backend code is hit in case the user is not logged in yet
          window.location.href = "/manage";
        }else if (locations.length == 1) {
          this.selectLocation(locations[0])
        } else {
          this.loading = false
        }
      },
      error: (err: DataError) => {
        this.displayError(err.message);
      }
    })
  }

  ngOnInit() { 
    this.refresh();
  }

  selectLocation(location: Location) {
    this.router.navigate(["view/"+location.name]);
  }
}

