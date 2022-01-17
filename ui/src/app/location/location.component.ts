import { MatSnackBar } from '@angular/material/snack-bar';

import { Component, OnInit } from '@angular/core';
import { DataService } from './../data.service';
import { Router, ActivatedRoute } from '@angular/router';

import { Location, Tap, Beer, Sensor, DataError } from './../models/models';
import { SensorData, TapDetails } from './models'

import * as _ from 'lodash';
//import * as $ from 'jquery';

@Component({
  selector: 'app-location',
  templateUrl: './location.component.html',
  styleUrls: ['./location.component.scss']
})
export class LocationComponent implements OnInit {
  title = 'Location';

  isLoading = false;
  location_identifier: any;
  location!: Location;
  taps: TapDetails[] = [];
  _ = _; //allow the html template to access lodash

  constructor(private dataService: DataService, private router: Router, private route: ActivatedRoute, private _snackBar: MatSnackBar) {
    this.route.params.subscribe( (params: any) => this.location_identifier = params['location'] );
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh() {
    this.isLoading = true;
    this.taps = [];
    this.dataService.getLocation(this.location_identifier).subscribe({
      next: (location: Location) => {
        this.location = location;
        this.dataService.getTaps(location.id).subscribe((taps: Tap[]) => {
          _.forEach(taps, (tap: Tap) => {
            let tapD = <TapDetails>tap;
            this.taps.push(tapD)
            this.setTapDetails(tapD);
          })
          this.isLoading = false;
        }, (err: DataError) => {
          this.displayError(err.message);
        })
      }, error: (err: DataError) => {
        if (err.statusCode === 404) {
          this.router.navigate(["/"]);
        }

        this.displayError(err.message);
      }
  })
  }

  // refreshTap(tapId: string) {
  //   this.dataService.getTap(tapId, this.location.id).subscribe((tap: Tap) => {
      
  //   })
  // }

  setTapDetails(tap: TapDetails) {
    tap.isEmpty = this.isTapEmpty(tap);
  
    if(!tap.isEmpty) {
      tap.isLoading = true
      if(tap.tapType === "beer"){
        this.dataService.getBeer(tap.beerId, tap.locationId).subscribe((beer: Beer) => {
          console.log(beer);
          tap.beer = beer;
          tap.isLoading = false;
        })
      }
      // fix when coldbrew is implemented
      if(tap.tapType === "cold-brew") {
        tap.isLoading = false;
      }

      if(!_.isEmpty(tap.sensorId)) {
        this.dataService.getSensor(tap.sensorId, tap.locationId).subscribe((sensor: Sensor) => {
          let sensorData = <SensorData>sensor;
          tap.sensor = sensorData;

          this.dataService.getPercentBeerRemaining(sensorData.id, sensorData.locationId).subscribe((val: number) => {
            console.log(val);
            sensorData.percentBeerRemaining = val as number;
            console.log(sensorData);
            console.log(tap.sensor);
          });
        })
      }
    }

    //setTimeout(() => {refreshTap(tap.id)}, _.random(600, 1200)*100);
  }

  isTapEmpty(tap: TapDetails) {
    if(_.isEmpty(tap.beerId) && _.isEmpty(tap.coldBrewId)){
      return true;
    }
    
    return false;
  }

  getSrm(beer: Beer) {
    if(_.isNil(beer)){
      return "1";
    }
    return beer.srm > 40 ? "40plus" : _.toString(_.round(beer.srm))
  }

  ngOnInit() {  
    this.refresh();
  }
}
