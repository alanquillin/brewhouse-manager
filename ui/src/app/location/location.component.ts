import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';

import { Component, OnInit, Inject } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { Location, Tap, Beer, Sensor, Settings, TapRefreshSettings, Beverage, ColdBrew, ImageTransitionalBase, Dashboard, DashboardSettings, Batch, UserInfo } from './../models/models';
import { isNilOrEmpty, openFullscreen, closeFullscreen } from '../utils/helpers';
import { ConfigService } from '../_services/config.service';
import { DataService, DataError } from '../_services/data.service';
import { SettingsService } from '../_services/settings.service';

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
    styleUrls: ['./location.component.scss'],
    standalone: false
})
export class LocationComponent implements OnInit {
  title = 'Location';

  isLoading = false;
  location_identifier: any;
  locations: Location[] = [];
  location!: Location;
  taps: TapDetails[] = [];
  isNilOrEmpty: Function = isNilOrEmpty;
  tapRefreshSettings: TapRefreshSettings = new TapRefreshSettings();
  dashboardSettings: DashboardSettings = new DashboardSettings();
  isFullscreen: boolean = false;
  enableFullscreen: boolean = false;
  serviceAvailable: boolean = true;
  lastServiceAvailDT: Date = new Date(Date.now());
  userInfo!: UserInfo;

  _ = _; //allow the html template to access lodash

  constructor(
    private dataService: DataService,
    private settingsService: SettingsService,
    private router: Router,
    private route: ActivatedRoute,
    private _snackBar: MatSnackBar,
    public dialog: MatDialog,
    private configService: ConfigService
  ) {
    this.route.params.subscribe( (params: any) => this.location_identifier = params['location'] );
  }

  scheduleHealthCheck(): void {
    setTimeout(() => {this.checkHealth()}, 30000);
  }

  checkHealth(next?: Function): void {
    this.dataService.isAvailable().subscribe({
      next: (res: any) => {
        this.serviceAvailable = true;
        this.lastServiceAvailDT = new Date(Date.now());
        this.scheduleHealthCheck();
        if(next) {
          next();
        }
      },
      error: (err: DataError) => {
        this.serviceAvailable = false;
        this.scheduleHealthCheck();
      }
    })
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(next?: Function, always?: Function) {
    this.isLoading = true;
    this.taps = [];
    
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;
        this._refresh(next, always);
      },
      error: (err: DataError) => {
        if(err.statusCode === 401) {
          this._refresh(next, always);
        } else {
          this.displayError(err.message);
        }
      },
      complete: () => {
      }
    });
  }

  _refresh(next?: Function, always?: Function) {
    this.settingsService.settings$.subscribe({
      next: (data: Settings) => {
        this.tapRefreshSettings = new TapRefreshSettings(data.taps.refresh);
        this.dashboardSettings = new DashboardSettings(data.dashboard);
        this.dataService.getDashboard(this.location_identifier).subscribe({
          next: (dashboard: Dashboard) => {
            this.location = new Location(dashboard.location);
            this.locations = [];
            for(let location of _.sortBy(dashboard.locations, (l) => {return l.description})) {
              this.locations.push(new Location(location));
            }
            this.taps = [];
            for(let tap of _.sortBy(dashboard.taps, (t) => {return t.tapNumber})) {
              let _tap = this.setTapDetails(new TapDetails(tap));
              this.taps.push(_tap);
              this.scheduleTapRefresh(_tap);
            }
            if(!_.isNil(next)) {
              next();
            }
            this.isLoading = false;
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

  scheduleTapRefresh(tap: TapDetails): void {
    const refreshInMs = (this.tapRefreshSettings.baseSec + _.random(this.tapRefreshSettings.variable * -1, this.tapRefreshSettings.variable))*1000;
    setTimeout(() => {this.refreshTap(tap)}, refreshInMs);
  }

  refreshTap(tap: TapDetails) {
    if(this.serviceAvailable) {
      this.dataService.getDashboardTap(tap.id).subscribe({
        next: (_tap: Tap) => {
          tap.from(_tap);
          tap = this.setTapDetails(tap);
          this.scheduleTapRefresh(tap);
        },
        error: (err: DataError) => {
          this.scheduleTapRefresh(tap);
        }
      });
    } else {
      this.scheduleTapRefresh(tap);
    }
  }

  setTapDetails(tap: TapDetails): TapDetails {
    tap.isEmpty = this.isTapEmpty(tap);

    if(!tap.isEmpty) {
      tap.isLoading = true
      tap.beer = new Beer();
      tap.beverage = new Beverage();

      if(!isNilOrEmpty(tap.batch)){
        tap.batch = new Batch(tap.batch)
      }

      if(tap.tapType === "beer"){
        this.dataService.getDashboardBeer(tap.beerId).subscribe((beer: Beer) => {
          const _beer = new Beer(beer)
          tap.beer = _beer;
        })
      }
      
      if(tap.tapType === "beverage") {
        this.dataService.getDashboardBeverage(tap.beverageId).subscribe((beverage: Beverage) => {
          tap.beverage = new Beverage(beverage);
          if(beverage.type === "cold-brew") {
            tap.coldBrew = new ColdBrew(beverage);
          }
        })
      }

      if(!_.isEmpty(tap.sensorId)) {
        this.dataService.getDashboardSensor(tap.sensorId).subscribe((sensor: Sensor) => {
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
    return tap;
  }

  isTapEmpty(tap: TapDetails): boolean {
    if(isNilOrEmpty(tap.beerId) && isNilOrEmpty(tap.beverageId) && isNilOrEmpty(tap.batchId)){
      return true;
    }
    
    return false;
  }

  getSrm(tap: Tap): string {
    var srm = 1
    if(!_.isNil(tap) && !_.isNil(tap.beer)){
      srm = tap.beer.getSrm(tap.batch);
    }
    
    return srm > 40 ? "40plus" : _.toString(_.round(srm))
  }

  ngOnInit() { 
    // const isIOS = /iPad|iPhone|iPod/.test(navigator.platform) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    // const isSafari = navigator.userAgent.indexOf("Safari") !== -1 && navigator.userAgent.indexOf("CriOS") === -1 && navigator.userAgent.indexOf("FxiOS") === -1

    // this.enableFullscreen = isIOS && isSafari;
    this.enableFullscreen = true;

    this.checkHealth(()=>{
      this.refresh(()=>{
        this.configService.update({title: `On Tap: ${this.location.description}`})
      })
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

  getImageUrl(tap: TapDetails): string {
    if(tap.isLoading) {
      return "";
    }
    
    let b: ImageTransitionalBase | undefined = tap.tapType === "beer" ? tap.beer : tap.beverage;

    if (!b) {
      return "";
    }

    let imageUrl = b.getImgUrl(tap.batch);
    if(!tap.sensor) {
      return imageUrl;
    }
    
    if(b.imageTransitionsEnabled) {
      let percentBeerRemaining = tap.sensor.percentBeerRemaining;

      if(isNilOrEmpty(percentBeerRemaining)) {
        return imageUrl;
      };

      if(percentBeerRemaining <= 0) {
        return b.emptyImgUrl;
      }
      
      if(b.imageTransitions && !isNilOrEmpty(b.imageTransitions)) {
        for(let i of b.imageTransitions) {
          if(percentBeerRemaining > i.changePercent) {
            break;
          }
          imageUrl = i.imgUrl;
        }
      }

      return imageUrl;
    } else {
      return imageUrl;
    }
  }

  toggleFullscreen() {
    if(this.isFullscreen)
      closeFullscreen(document);
    else
      openFullscreen(document);
      

    this.isFullscreen = !this.isFullscreen;
  }

  goto(path: string): void {
    if(path === 'home') {
      path = "";
    }
    window.location.href = `/${path}`;
  }

  get showHomeBtn() : boolean {
    if (this.locations.length > 1) {
      return true;
    }
    return false;
  }

  get loggedIn() : Boolean {
    if (this.isNilOrEmpty(this.userInfo)) {
      return false;
    }
    return true;
  }
}
