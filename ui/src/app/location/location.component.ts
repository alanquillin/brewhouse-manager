import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';

import { Component, OnInit, Inject } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { Location, Tap, Beer, Sensor, Settings, TapRefreshSettings, TapSettings } from './../models/models';
import { isNilOrEmpty } from '../utils/helpers';
import { ConfigService } from '../_services/config.service';
import { DataService, DataError } from '../_services/data.service';

import { LocationImageDialog } from '../_dialogs/image-preview-dialog/image-preview-dialog.component'
import { LocationQRCodeDialog } from '../_dialogs/qrcode-dialog/qrcode-dialog.component'

import * as _ from 'lodash';

export class TapDetails extends Tap {
  isEmpty!: boolean;
  isLoading!: boolean;
  override sensor!: SensorData;

  constructor(from?: any) {
    super(from);
  }

  get showTotalBeerRemaining(): boolean {
    if(isNilOrEmpty(this.sensor)){
      return false;
    }

    return this.sensor.totalBeerRemaining > 0;
  }
}

export class SensorData extends Sensor {
  percentBeerRemaining: number = 0;
  totalBeerRemaining: number = 0;
  beerRemainingUnit: string = "";
}

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
  isNilOrEmpty: Function = isNilOrEmpty;
  tapRefreshSettings: TapRefreshSettings = new TapRefreshSettings();

  _ = _; //allow the html template to access lodash

  constructor(private dataService: DataService, private router: Router, private route: ActivatedRoute, private _snackBar: MatSnackBar, public dialog: MatDialog, private configService: ConfigService) {
    this.route.params.subscribe( (params: any) => this.location_identifier = params['location'] );
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(next?: Function, always?: Function) {
    this.isLoading = true;
    this.taps = [];

    this.dataService.getSettings().subscribe({
      next: (data: Settings) => {
        this.tapRefreshSettings = new TapRefreshSettings(data.taps.refresh);

        this.dataService.getLocation(this.location_identifier).subscribe({
          next: (location: Location) => {
            this.location = location;


            this.dataService.getTaps(location.id).subscribe({
              next: (taps: Tap[]) => {
                _.forEach(taps, (tap: Tap) => {
                  this.taps.push(this.setTapDetails(new TapDetails(tap)))
                })
                this.taps = _.sortBy(this.taps, (t) => {return t.tapNumber});
                this.isLoading = false;
                if(!_.isNil(next)){
                  next();
                }
              },
              error: (err: DataError) => {
                this.displayError(err.message);
                if(!_.isNil(always)) {
                  always();
                }
              }
            });



          }, error: (err: DataError) => {
            if (err.statusCode === 404) {
              this.router.navigate(["/"]);
            }
    
            this.displayError(err.message);
            if(!_.isNil(always)) {
              always();
            }
          }
        });
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if(!_.isNil(always)) {
          always();
        }
      }
    });
  }

  refreshTap(tap: TapDetails) {
    this.dataService.getTap(tap.id).subscribe((_tap: Tap) => {
      tap.from(_tap);
      this.setTapDetails(tap);
    })
  }

  setTapDetails(tap: TapDetails): TapDetails {
    tap.isEmpty = this.isTapEmpty(tap);
  
    if(!tap.isEmpty) {
      tap.beer = new Beer(tap.beer);
      tap.isLoading = true
      if(tap.tapType === "beer"){
        this.dataService.getBeer(tap.beerId).subscribe((beer: Beer) => {
          const _beer = new Beer(beer)
          tap.beer = _beer;
        })
      }
      // fix when coldbrew is implemented
      if(tap.tapType === "cold-brew") {
        tap.isLoading = false;
      }

      if(!_.isEmpty(tap.sensorId)) {
        this.dataService.getSensor(tap.sensorId).subscribe((sensor: Sensor) => {
          let sensorData = <SensorData>sensor;
          tap.sensor = sensorData;

          this.dataService.getPercentBeerRemaining(sensorData.id).subscribe((val: number) => {
            sensorData.percentBeerRemaining = val as number;
            tap.isLoading = false;
          });
          this.dataService.getTotalBeerRemaining(sensorData.id).subscribe((val: number) => {
            sensorData.totalBeerRemaining = val as number;
            tap.isLoading = false;
          });
          this.dataService.getBeerRemainingUnit(sensorData.id).subscribe((val: string) => {
            sensorData.beerRemainingUnit = val;
            tap.isLoading = false;
          });
        })
      } else {
        tap.isLoading = false;
      }
    }

    const refreshInMs = (this.tapRefreshSettings.baseSec + _.random(this.tapRefreshSettings.variable * -1, this.tapRefreshSettings.variable))*1000;
    setTimeout(() => {this.refreshTap(tap)}, refreshInMs);
    return tap;
  }

  isTapEmpty(tap: TapDetails): boolean {
    if(_.isEmpty(tap.beerId)){
      return true;
    }
    
    return false;
  }

  getSrm(beer: Beer): string {
    if(_.isNil(beer)){
      return "1";
    }
    const srm = beer.getSrm();
    return srm > 40 ? "40plus" : _.toString(_.round(srm))
  }

  ngOnInit() { 
    console.log(window.navigator.userAgent);
    // if(window.navigator.userAgent.match(/(iPod|iPhone|iPad)/)) {
    //   console.log("attempting to fullscreen");
    //   let elem = document.documentElement;
    //   if (elem.requestFullscreen) {
    //     console.log("calling full screen");
    //     elem.requestFullscreen();
    //   }
      // else if (elem.mozRequestFullScreen) {
      //   /* Firefox */
      //   elem.mozRequestFullScreen();
      // } else if (elem.webkitRequestFullscreen) {
      //   /* Chrome, Safari and Opera */
      //   elem.webkitRequestFullscreen();
      // } else if (elem.msRequestFullscreen) {
      //   /* IE/Edge */
      //   elem.msRequestFullscreen();
      // }
    // }
    
    this.refresh(()=>{
      this.configService.update({title: `On Tap: ${this.location.description}`})
    });
  }

  openImageDialog(imgUrl: string) {
    this.dialog.open(LocationImageDialog, {
      data: {
        imgUrl: imgUrl,
      },
    });
  }

  openQRCodeDialog(url: string) {
    this.dialog.open(LocationQRCodeDialog, {
      data: {
        url: url,
        title: "Check-in on Untappd"
      },
    });
  }

  getUntappdUrl(beer: Beer): string {
    if(isNilOrEmpty(beer) || isNilOrEmpty(beer.untappdId)){
      return "";
    }

    return `https://untappd.com/qr/beer/${beer.untappdId}`;
  }

  getRemainingBeerValue(tap: TapDetails): number {
    if (isNilOrEmpty(tap.sensor.percentBeerRemaining)) {
      return 0;
    }

    return tap.sensor.percentBeerRemaining;
  }
}
