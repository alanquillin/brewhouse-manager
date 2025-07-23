import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { UntypedFormControl, AbstractControl, Validators, UntypedFormGroup } from '@angular/forms';

import { Sensor, Location, UserInfo, SensorDiscoveryData, SensorData } from '../../models/models';

import { isNilOrEmpty } from '../../utils/helpers'

import * as _ from 'lodash';

@Component({
    selector: 'app-sensors',
    templateUrl: './sensors.component.html',
    styleUrls: ['./sensors.component.scss'],
    standalone: false
})
export class ManageSensorsComponent implements OnInit {

  loading = false;
  sensors: Sensor[] = [];
  filteredSensors: Sensor[] = [];
  locations: Location[] = [];
  sensorTypes: string[] = [];
  processing = false;
  adding = false;
  editing = false;
  modifySensor: Sensor = new Sensor();
  _ = _;
  selectedLocationFilters: string[] = [];
  sensorDiscoveryData: SensorDiscoveryData[] = [];
  sensoryDiscoveryProcessing = false;
  selectedDiscoveredSensorId: any;

  userInfo!: UserInfo;

  modifyFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [Validators.required]),
    sensorType: new UntypedFormControl('', [Validators.required]),
    locationId: new UntypedFormControl('', [Validators.required]),
    metaAuthToken: new UntypedFormControl('', []),
    kvmDevice: new UntypedFormControl('', [])
  });

  get displayedColumns(): string[] {
    var cols = ['name', 'type'];

    if(this.locations.length > 1) {
      cols.push("location")
    }

    return _.concat(cols, ['actions']);
  }

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
          var _sensor = new Sensor(sensor)
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
        this.locations = _.sortBy(locations, [(l:Location) => {return l.description}]);
        this.dataService.getSensorTypes().subscribe({
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
    var data: any = {}
    if(this.locations.length === 1){
      data["locationId"] = this.locations[0].id;
    }
    if(this.sensorTypes.length === 1) {
      data["sensorType"] = this.sensorTypes[0];
    }

    this.modifySensor = new Sensor(data);
    this.modifySensor.editValues = data;
    this.adding = true;
  }

  create(): void {
    this.processing = true;
    var meta : any = {}
    console.log(this.modifySensor);
    if(this.modifySensor.editValues.sensorType == "plaato-keg") {
      meta.authToken = this.modifySensor.editValues.meta.authToken;
    } else if (this.modifySensor.editValues.sensorType == "keg-volume-monitor-weight" || this.modifySensor.editValues.sensorType == "keg-volume-monitor-flow") {
      meta.deviceId = this.selectedDiscoveredSensorId;
    } else if (this.modifySensor.editValues.sensorType == "kegtron-pro") {
      meta.deviceId = this.modifySensor.editValues.meta.deviceId
      meta.portNum = _.toInteger(this.modifySensor.editValues.portNum);
      meta.accessToken = this.modifySensor.editValues.accessToken;
    }

    var data: any = {
      name: this.modifySensor.editValues.name,
      sensorType: this.modifySensor.editValues.sensorType,
      locationId: this.modifySensor.editValues.locationId,
      meta: meta
    }
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
    if (this.modifySensor.editValues.sensorType !== "plaato-keg") {
      this.discoverSensors(() => {
        if(!isNilOrEmpty(this.modifySensor.editValues.meta)) {
          if (this.modifySensor.editValues.sensorType == "keg-volume-monitor-weight" || this.modifySensor.editValues.sensorType == "keg-volume-monitor-flow") {
            this.selectedDiscoveredSensorId = _.get(this.modifySensor.editValues.meta, 'deviceId');
          } else if (this.modifySensor.editValues.sensorType == "kegtron-pro") {
            let deviceId = _.get(this.modifySensor.editValues.meta, 'deviceId');
            let portNum = _.get(this.modifySensor.editValues.meta, 'portNum');
            this.selectedDiscoveredSensorId = deviceId + "|" + portNum;
          }
        }
      });
    }
  }

  save(): void {
    this.processing = true;
    console.log(this.modifySensor);
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
    
    filteredData = _.sortBy(filteredData, [(d: Sensor) => {
        if(sortBy === "location"){
          return _.isNil(d.location) ? "" : d.location.name
        }
        return _.get(d, sortBy);
      }]);
    if(!asc){
      _.reverse(filteredData);
    }
    this.filteredSensors = filteredData;
  }

  sensorTypeChanged() {
    if (this.modifySensor.editValues.sensorType !== "plaato-keg") {
      this.discoverSensors();
    }
  }

  discoverSensors(next?: Function) {
    this.sensorDiscoveryData = [];
    this.sensoryDiscoveryProcessing = true;
    this.dataService.discoverSensors(this.modifySensor.editValues.sensorType).subscribe({
      next: (data: SensorDiscoveryData[]) => {
        this.sensorDiscoveryData = data;
        if(!_.isNil(next)){
          next();
        }
        this.sensoryDiscoveryProcessing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.sensoryDiscoveryProcessing = false;
      }
    });
  }

  selectedDiscoveredSenorChange() {
    console.log("device changed");
    if (this.modifySensor.editValues.sensorType == "keg-volume-monitor-weight" || this.modifySensor.editValues.sensorType == "keg-volume-monitor-flow") {
      this.modifySensor.editValues.meta.deviceId = this.selectedDiscoveredSensorId;
    } else if (this.modifySensor.editValues.sensorType == "kegtron-pro") {
      let parts = _.split(this.selectedDiscoveredSensorId, "|");
      this.modifySensor.editValues.meta.deviceId = parts[0];
      this.modifySensor.editValues.meta.portNum = _.toInteger(parts[1]);
      _.forEach(this.sensorDiscoveryData, (dev) => {
        if(dev.id === this.modifySensor.editValues.meta.deviceId && dev.portNum === this.modifySensor.editValues.meta.portNum) {
          this.modifySensor.editValues.meta.accessToken = dev.token;
        }
      });
    }
    console.log(this.modifySensor);
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  }

}
