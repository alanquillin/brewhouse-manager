import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService } from '../../data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { FormControl, AbstractControl, Validators, FormGroup } from '@angular/forms';

import { Beer, DataError, Location, Tap, Sensor } from '../../models/models';

import * as _ from 'lodash';

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
  displayedColumns: string[] = ['description', 'tapNumber', 'beer', 'location', 'sensor', 'actions'];
  loading = false;
  processing = false;
  adding = false;
  editing = false;
  modifyTap: Tap = new Tap();
  _ = _;
  selectedLocationFilters: string[] = [];

  modifyFormGroup: FormGroup = new FormGroup({
    description: new FormControl('', [Validators.required]),
    locationId: new FormControl('', [Validators.required]),
    beerId: new FormControl(''),
    tapNumber: new FormControl('', [Validators.required, Validators.pattern("^[0-9]*$")]),
    sensorId: new FormControl(''),
  });

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
          var _tap = new Tap()
          Object.assign(_tap, tap);
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
        this.locations = _.orderBy(locations, ["name"]);
        this.dataService.getBeers().subscribe({
          next: (beers: Beer[]) => {
            this.beers = beers;
            this.dataService.getSensors().subscribe({
              next: (sensors: Sensor[]) => {
                this.sensors = sensors;
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
    this.refreshAll(()=> {
      this.loading = false;
    })
  }

  add(): void {
    this.modifyFormGroup.reset();
    this.modifyTap = new Tap();
    this.adding = true;
  }

  create(): void {
    var data: any = {
      description: this.modifyTap.editValues.description,
      tapNumber: this.modifyTap.editValues.tapNumber,
      locationId: this.modifyTap.editValues.locationId,
      tapType: "beer",
    }

    if(!_.isNil(this.modifyTap.editValues.beerId) && this.modifyTap.editValues.beerId !== "-1") {
      data["beerId"] = this.modifyTap.editValues.beerId;
    }

    if(!_.isNil(this.modifyTap.editValues.sensorId) && this.modifyTap.editValues.sensorId !== "-1") {
      data["sensorId"] = this.modifyTap.editValues.sensorId;
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
          this.refresh(()=>{ this.processing = false; });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
    }
  }

  filter(sort?: Sort): void {
    var sortBy:string = "description";
    var asc: boolean = true;
    if(!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    var filteredData: Tap[] = this.taps;
    if(!_.isEmpty(this.selectedLocationFilters)){
      filteredData = <Tap[]>_.filter(this.taps, (s) => { return this.selectedLocationFilters.includes(s.locationId) });
    }
    filteredData = _.orderBy(filteredData, [sortBy], [asc])
    _.sortBy(filteredData, [(d: Tap) => {
        if(sortBy === "location"){
          return _.isNil(d.location) ? "" : d.location.name
        }
        if(sortBy === "sensor"){
          return _.isNil(d.sensor) ? "" : d.sensor.name
        }
        if(sortBy === "beer"){
          return _.isNil(d.beer) ? "" : d.beer.name
        }
        return _.get(sortBy, sortBy);
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

  getBeerName(beer: Beer | undefined, beerId?: string): string {
    if(_.isNil(beer) && !_.isNil(beerId)){
      beer = _.find(this.beers, (b) => {return b.id == beerId});
    }
    if(_.isNil(beer)) {
      return "";
    }
    var name = beer.name;
    var tool = beer.externalBrewingTool;
    var batchNumber: string | undefined
    var style = beer.style;
    if(!_.isEmpty(tool)){
      if(!_.isEmpty(beer.externalBrewingToolMeta)){
        if(_.isEmpty(name)){
          name = _.get(beer.externalBrewingToolMeta, 'details.name')
        }
        if(_.isEmpty(style)){
          style = _.get(beer.externalBrewingToolMeta, 'details.style')
        }
        batchNumber = _.get(beer.externalBrewingToolMeta, 'details.batchNumber')
      }
    }

    if(_.isEmpty(name)) {
      name = "--NO NAME--";
    }
    if(!_.isEmpty(style)){
      name = `${name} [${style}]`;
    }
    if(!_.isEmpty(tool)) {
      if (!_.isEmpty(_.toString(batchNumber))){
        tool = `${tool} - batch #${batchNumber})`;
      }
      name = `${name} (${tool})`
    }

    return name;
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

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  } 
}
