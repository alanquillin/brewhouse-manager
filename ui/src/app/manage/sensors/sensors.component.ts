import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService } from '../../data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { FormControl, AbstractControl, Validators, FormGroup } from '@angular/forms';

import { Sensor, DataError, Location } from '../../models/models';

import * as _ from 'lodash';

@Component({
  selector: 'app-sensors',
  templateUrl: './sensors.component.html',
  styleUrls: ['./sensors.component.scss']
})
export class ManageSensorsComponent implements OnInit {

  sensors: Sensor[] = [];
  filteredSensors: Sensor[] = [];
  locations: Location[] = [];
  sensorTypes: string[] = [];
  displayedColumns: string[] = ['name', 'type', 'location', 'actions'];
  processing = false;
  adding = false;
  editing = false;
  modifySensor: Sensor = new Sensor();
  _ = _;
  selectedLocationFilters: string[] = [];

  modifyFormGroup: FormGroup = new FormGroup({
    name: new FormControl('', [Validators.required]),
    sensorType: new FormControl('', [Validators.required]),
    locationId: new FormControl('', [Validators.required]),
    metaAuthToken: new FormControl('', [Validators.required])
  });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getSensors().subscribe({
      next: (sensors: Sensor[]) => {
        this.sensors = [];
        _.forEach(sensors, (sensor) => {
          var _sensor = new Sensor()
          Object.assign(_sensor, sensor);
          this.sensors.push(_sensor)
        })
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
        this.dataService.getSensorType().subscribe({
          next: (sensorTypes: string[]) => {
            this.sensorTypes = _.orderBy(sensorTypes, ["name"]);
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
  }

  ngOnInit(): void {
    this.processing = true;
    this.refreshAll(()=> {
      this.processing = false;
    })
  }

  add(): void {
    this.modifyFormGroup.reset();
    this.modifySensor = new Sensor();
    this.adding = true;
  }

  create(): void {
    console.log(this.modifySensor);
    this.processing = true;
    var data: any = {
      name: this.modifySensor.editValues.name,
      sensorType: this.modifySensor.editValues.sensorType,
      locationId: this.modifySensor.editValues.locationId,
      meta: {authToken: this.modifySensor.editValues.meta.authToken}
    }
    console.log(`Creating sensor`)
    console.log(data)
    this.dataService.createSensor(data).subscribe({
      next: (sensor: Sensor) => {
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

  edit(sensor: Sensor): void {
    sensor.enableEditing();
    this.modifySensor = sensor;
    this.editing = true;
    this.modifyFormGroup.reset();
  }

  save(): void {
    this.processing = true;
    this.dataService.updateSensor(this.modifySensor.id, this.modifySensor.changes).subscribe({
      next: (sensor: Sensor) => {
        this.modifySensor.disableEditing();
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
    this.modifySensor.disableEditing();
    this.editing = false;
  }

  delete(sensor: Sensor): void {
    if(confirm(`Are you sure you want to delete sensor '${sensor.name}'?`)) {
      this.processing = true;
      this.dataService.deleteSensor(sensor.id).subscribe({
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

  getLocationName(sensor: Sensor): string {
    var loc = _.find(this.locations, (l) => {return l.id === sensor.locationId;})

    if(_.isNil(loc) || _.isEmpty(loc)){
      return "UNKNOWN";
    }

    return (loc as Location).name;
  }

  filter(sort?: Sort) {
    var sortBy:string = "description";
    var asc: boolean = true;

    if(!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    var filteredData: Sensor[] = this.sensors;
    if(!_.isEmpty(this.selectedLocationFilters)){
      filteredData = <Sensor[]>_.filter(this.sensors, (s) => { return this.selectedLocationFilters.includes(s.locationId) });
    }
    filteredData = _.orderBy(filteredData, [sortBy], [asc])
    _.sortBy(filteredData, [(d: Sensor) => {
        if(sortBy === "location"){
          return _.isNil(d.location) ? "" : d.location.name
        }
        return _.get(sortBy, sortBy);
      }]);
    if(!asc){
      _.reverse(filteredData);
    }
    this.filteredSensors = filteredData;
  }

  addMissingMeta() {
    switch(this.modifySensor.editValues.sensorType) {
      case "plaato-keg":
        if(!_.has(this.modifySensor.editValues.meta, "authToken")){
          console.log("adding missing metadata");
          console.log(this.modifySensor.editValues.meta)
          _.set(this.modifySensor.editValues, 'meta.authToken', '');
          console.log(this.modifySensor);
        }
        break
    }
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  }  
}
