import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { FormControl, AbstractControl, Validators, FormGroup } from '@angular/forms';

import { Beer, Beverage, Location, Tap, Sensor, UserInfo } from '../../models/models';

import * as _ from 'lodash';
import { isNilOrEmpty } from 'src/app/utils/helpers';

@Component({
  selector: 'app-taps',
  templateUrl: './taps.component.html',
  styleUrls: ['./taps.component.scss']
})
export class ManageTapsComponent implements OnInit {

  taps: Tap[] = []
  filteredTaps: Tap[] = [];
  locations: Location[] = [];
  beers: Beer[] = [];
  sensors: Sensor[] = [];
  beverages: Beverage[] = [];
  loading = false;
  processing = false;
  adding = false;
  editing = false;
  modifyTap: Tap = new Tap();
  _ = _;
  selectedLocationFilters: string[] = [];
  isNilOrEmpty = isNilOrEmpty;

  userInfo!: UserInfo;

  modifyFormGroup: FormGroup = new FormGroup({
    displayName: new FormControl('', []),
    description: new FormControl('', [Validators.required]),
    locationId: new FormControl('', [Validators.required]),
    beerId: new FormControl(''),
    tapNumber: new FormControl('', [Validators.required, Validators.pattern("^[0-9]*$")]),
    sensorId: new FormControl(''),
    beverageId: new FormControl(''),
    namePrefix: new FormControl('', []),
    nameSuffix: new FormControl('', [])
  });

  get displayedColumns() {
    var cols = ['displayName', 'description', 'tapNumber'];

    if(this.locations.length > 1) {
      cols.push('location');
    }

    return _.concat(cols, ['beer', 'beverage', 'sensor', 'actions']);
  }

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getTaps().subscribe({
      next: (taps: Tap[]) => {
        this.taps = [];
        _.forEach(taps, (tap) => {
          var _tap = new Tap(tap)
          if (!isNilOrEmpty(_tap.beer)) {
            _tap.beer = new Beer(_tap.beer);
          }
          if (isNilOrEmpty(_tap.beer) && !isNilOrEmpty(_tap.beerId)) {
            _tap.beer = this.findBeer(_tap.beerId);
          }
          
          if (!isNilOrEmpty(_tap.beverage)) {
            _tap.beverage = new Beverage(_tap.beverage);
          }
          if (isNilOrEmpty(_tap.beverage) && !isNilOrEmpty(_tap.beverageId)) {
            _tap.beverage = this.findBeverage(_tap.beverageId);
          }
          this.taps.push(_tap)
        });
        this.filter();
      }, 
      error: (err: DataError) => {
        this.displayError(err.message);
        if(!_.isNil(error)){
          error();
        }
        if(!_.isNil(always)){
          always();
        }
      },
      complete: () => {
        if(!_.isNil(next)){
          next();
        }
        if(!_.isNil(always)){
          always();
        }
      }
    })
  }

  refreshAll(always?:Function, next?: Function, error?: Function) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = _.sortBy(locations, [(l:Location) => {return l.description}]);
        this.dataService.getBeers().subscribe({
          next: (beers: Beer[]) => {
            this.beers = []
            _.forEach(beers, (beer) => {
              this.beers.push(new Beer(beer));
            });
            this.beers = _.sortBy(this.beers, (beer) => { return beer.getName(); });
            this.dataService.getSensors().subscribe({
              next: (sensors: Sensor[]) => {
                this.sensors = sensors;
                this.dataService.getBeverages().subscribe({
                  next: (beverages: Beverage[]) => {
                    this.beverages = [];
                    _.forEach(_.sortBy(beverages, ["name"]), (beverage) => {
                      this.beverages.push(new Beverage(beverage));
                    });
                    this.refresh(always, next, error);
                  },
                  error: (err:DataError) => {
                    this.displayError(err.message);
                    if(!_.isNil(error)){
                      error();
                    }
                    if(!_.isNil(always)){
                      always();
                    }
                  }
                })
              },
              error: (err:DataError) => {
                this.displayError(err.message);
                if(!_.isNil(error)){
                  error();
                }
                if(!_.isNil(always)){
                  always();
                }
              }
            })
          },
          error: (err:DataError) => {
            this.displayError(err.message);
            if(!_.isNil(error)){
              error();
            }
            if(!_.isNil(always)){
              always();
            }
          }
        });
      },
      error: (err:DataError) => {
        this.displayError(err.message);
        if(!_.isNil(error)){
          error();
        }
        if(!_.isNil(always)){
          always();
        }
      }
    });
  }

  ngOnInit(): void {
    this.loading = true;
    
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;

        if(this.userInfo.locations && this.userInfo.admin) {
          for(let l of this.userInfo.locations) {
            this.selectedLocationFilters.push(l.id);
          }
        }
        this.refreshAll(()=> {
          this.loading = false;
        });
      },
      error: (err: DataError) => {
        if(err.statusCode !== 401) {
          this.displayError(err.message);
        }
      }
    });
  }

  add(): void {
    this.modifyFormGroup.reset();
    var data:any = {}
    if(this.locations.length === 1) {
      data["locationId"] = this.locations[0].id;
    }
    this.modifyTap = new Tap(data);
    this.modifyTap.editValues = data;
    this.adding = true;
  }

  create(): void {
    var data: any = {
      description: this.modifyTap.editValues.description,
      tapNumber: this.modifyTap.editValues.tapNumber,
      locationId: this.modifyTap.editValues.locationId,
      namePrefix: this.modifyTap.editValues.namePrefix,
      nameSuffix: this.modifyTap.editValues.nameSuffix
    }

    if(!_.isNil(this.modifyTap.editValues.beerId) && this.modifyTap.editValues.beerId !== "-1") {
      data["beerId"] = this.modifyTap.editValues.beerId;
    }

    if(!_.isNil(this.modifyTap.editValues.sensorId) && this.modifyTap.editValues.sensorId !== "-1") {
      data["sensorId"] = this.modifyTap.editValues.sensorId;
    }

    if(!_.isNil(this.modifyTap.editValues.beverageId) && this.modifyTap.editValues.beverageId !== "-1") {
      data["beverageId"] = this.modifyTap.editValues.beverageId;
    }

    this.processing = true;
    this.dataService.createTap(data).subscribe({
      next: (tap: Tap) => {
        this.refresh(() => {this.processing = false;}, () => {this.adding = false;});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  cancelAdd(): void {
    this.adding = false;
  }

  edit(tap: Tap): void {
    tap.enableEditing();
    this.modifyTap = tap;
    this.editing = true;
    this.modifyFormGroup.reset();
  }

  save(): void {
    var updateData:any = _.cloneDeep(this.modifyTap.changes);

    if(_.has(updateData, "beerId") && (updateData.beerId === "-1" || _.isNil(updateData.beerId))){
      updateData.beerId = null;
    }

    if(_.has(updateData, "sensorId") && (updateData.sensorId === "-1" || _.isNil(updateData.sensorId))){
      updateData.sensorId = null;
    }

    if(_.has(updateData, "beverageId") && (updateData.beverageId === "-1" || _.isNil(updateData.beverageId))){
      updateData.beverageId = null;
    }

    this.processing = true;
    this.dataService.updateTap(this.modifyTap.id, updateData).subscribe({
      next: (tap: Tap) => {
        this.modifyTap.disableEditing();
        this.refresh(()=> {this.processing = false;}, () => {
          this.editing = false;
        })
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  cancelEdit(): void {
    this.modifyTap.disableEditing();
    this.editing = false;
  }

  delete(tap: Tap): void {
    if(confirm(`Are you sure you want to delete tap #${tap.tapNumber} (${tap.description}) from '${_.isNil(tap.location) ? 'UNKNOWN' : tap.location.name}'?`)) {
      this.processing = true;
      this.dataService.deleteTap(tap.id).subscribe({
        next: (resp: any) => {
          this.processing = false;
          this.loading = true;
          this.refresh(()=>{ this.loading = false; });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
    }
  }

  filter(sort?: Sort): void {
    var sortBy:string = "tapNumber";
    var asc: boolean = true;
    if(!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    var filteredData: Tap[] = this.taps;
    if(!_.isEmpty(this.selectedLocationFilters)){
      filteredData = <Tap[]>_.filter(this.taps, (s) => { return this.selectedLocationFilters.includes(s.locationId) });
    }
  
    filteredData = _.sortBy(filteredData, [(d: Tap) => {
        if(sortBy === "location"){
          return _.isNil(d.location) ? "" : d.location.name
        }
        if(sortBy === "sensor"){
          return _.isNil(d.sensor) ? "" : d.sensor.name
        }
        if(sortBy === "beer"){
          return _.isNil(d.beer) ? "" : d.beer.getName();
        }
        return _.get(d, sortBy);
      }]);
    if(!asc){
      _.reverse(filteredData);
    }
    this.filteredTaps = filteredData;
  }

  getSensorName(sensor: Sensor | undefined, sensorId?: string): string {
    if(_.isNil(sensor) && !_.isNil(sensorId)){
      sensor = _.find(this.sensors, (s) => {return s.id === sensorId});
    }
    if(_.isNil(sensor)) {
      return "";
    }
    var name = sensor.name
    if(_.isEmpty(name)) {
      name = "UNNAMED";
    }
    return `${name} (${sensor.sensorType})`
  }

  findBeer(beerId: string) {
    return _.find(this.beers, (b) => {return b.id == beerId});
  }

  getBeerName(beer: Beer | undefined, beerId?: string): string {
    if(_.isNil(beer) && !_.isNil(beerId)){
      beer = this.findBeer(beerId);
    }
    if(_.isNil(beer)) {
      return "";
    }
    var name = beer.getName();
    var style = beer.getStyle();

    if(!_.isEmpty(style)){
      name = `${name} [${style}]`;
    }

    return name;
  }

  getUniqueBeerName(beer: Beer | undefined, beerId?: string): string {
    if(_.isNil(beer) && !_.isNil(beerId)){
      beer = this.findBeer(beerId);
    }
    if(_.isNil(beer)) {
      return "";
    }

    let name: string = this.getBeerName(beer);
    const beers: Beer[] = _.filter(this.beers, (b) => {return this.getBeerName(b).trim() === name.trim()});

    if (beers.length <= 1)
      return name;
    
    var tool = beer.externalBrewingTool;
    var batchNumber: string | undefined
    if(!_.isEmpty(tool)){
      if(!_.isEmpty(beer.externalBrewingToolMeta)){
        if(_.isEmpty(name)){
          name = _.get(beer.externalBrewingToolMeta, 'details.name')
        }
        batchNumber = _.get(beer.externalBrewingToolMeta, 'details.batchNumber')
      }

      if(_.isEmpty(tool)) {
        tool = "--UNKNOWN EXTERNAL TOOL--";
      } else {
        if (!_.isEmpty(_.toString(batchNumber))){
          tool = `${tool} - batch #${batchNumber})`;
        }
      }

      return `${name} (${tool})`;
    }
    
    return `${name} (${beer.getAbv()} alc./vol., brewed on: ${beer.getBrewDate()})`;
  }

  findBeverage(beverageId: string) {
    return _.find(this.beverages, (b) => {return b.id == beverageId});
  }

  getBeverageName(beverage: Beverage | undefined, beverageId?: string): string {
    if(_.isNil(beverage) && !_.isNil(beverageId)){
      beverage = this.findBeverage(beverageId);
    }
    
    if(_.isNil(beverage)) {
      return "";
    }

    return beverage.name;
  }

  getUniqueBeverageName(beverage: Beverage | undefined, beverageId?: string): string {
    if(_.isNil(beverage) && !_.isNil(beverageId)) {
      beverage = this.findBeverage(beverageId);
    }

    if(_.isNil(beverage)) {
      return "";
    }

    const name: string = beverage.name;
    const beverages : Beverage[] = _.filter(this.beverages, (b) => {return b.name.trim() === name.trim()});

    if (beverages.length <= 1)
      return name;

    return `${name} (Brewed by ${beverage.brewery} on ${beverage.getBrewDateDisplay()})`
  }

  getSensorsForLocation(locationId: string | undefined): Sensor[] {
    if(_.isNil(locationId)) {
      return [];
    }

    var sensors = _.filter(this.sensors, (s) => { return s.locationId === locationId});
    if(_.isNil(sensors)){
      return [];
    }
    return sensors;
  }

  getBeersForLocation(locationId: string | undefined) : Beer[] {
    if(_.isNil(locationId)) {
      return [];
    }

    var beers = _.filter(this.beers, (s) => { return s.locationId === locationId});
    if(_.isNil(beers)){
      return [];
    }
    return beers;
  }

  getBeveragesForLocation(locationId: string | undefined) : Beverage[] {
    if(_.isNil(locationId)) {
      return [];
    }

    var beverages = _.filter(this.beverages, (s) => { return s.locationId === locationId});
    if(_.isNil(beverages)){
      return [];
    }
    return beverages;
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  }

  showDisplayNameToolTip(tap: Tap) {
    return !isNilOrEmpty(tap.namePrefix) && !isNilOrEmpty(tap.nameSuffix);
  }

  clear(tap: Tap) {
    if(confirm(`Are you sure you want to clear the tap?`)) {
      this.processing = true;
      this.dataService.updateTap(tap.id, {beerId: null, beverageId:null}).subscribe({
        next: (resp: any) => {
          this.processing = false;
          this.loading = true;
          this.refresh(()=>{ this.loading = false; });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
    }
  }
}
