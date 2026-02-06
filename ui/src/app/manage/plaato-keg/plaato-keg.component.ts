import { Component, OnInit, ViewChild } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort } from '@angular/material/sort';
import { UntypedFormControl, UntypedFormGroup, Validators } from '@angular/forms';
import { PlaatoKegDevice, UserInfo, PlaatoDeviceResponse } from '../../models/models';
import { forkJoin, Observable } from 'rxjs';
import * as _ from 'lodash';
import { isNilOrEmpty } from 'src/app/utils/helpers';

@Component({
  selector: 'app-plaato-keg',
  templateUrl: './plaato-keg.component.html',
  styleUrls: ['./plaato-keg.component.scss'],
  standalone: false
})
export class ManagePlaatoKegComponent implements OnInit {
  loading = false;
  devices: PlaatoKegDevice[] = [];
  filteredDevices: PlaatoKegDevice[] = [];
  processing = false;
  processingModeChange = false;
  processingUnitTypeChange = false;
  processingUnitModeChange = false;
  processingSetEmptyKegWeight = false;
  processingSetMaxKegVolume = false;
  processingNewDevice = false;
  processingDeviceConfig = false;
  deviceConnectionVerified = false
  editing = false;
  modifyDevice: PlaatoKegDevice = new PlaatoKegDevice();
  userInfo!: UserInfo;
  textNewDevCounter = 0;
  iframeUrl = "";
  _ = _;
  isNilOrEmpty = isNilOrEmpty;

  // Setup new device state
  setupMode = false;
  setupDevice: PlaatoKegDevice = new PlaatoKegDevice();
  deviceConfig: any = {}
  showWifiPassword = false;

  modifyFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', []),
  });

  setupFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [Validators.required]),
  });

  configureDeviceFormGroup: UntypedFormGroup = new UntypedFormGroup({
    wifiSsid: new UntypedFormControl('', []),
    wifiPassword: new UntypedFormControl('', [])
  });

  @ViewChild(MatSort) sort!: MatSort;

  get displayedColumns(): string[] {
    return ['name', 'id', 'connected', 'beerLeft', 'mode', 'unitDetails', 'firmware', 'wifiStrength', 'lastUpdatedOn', 'actions'];
  }

  constructor(
    private dataService: DataService,
    private settingsService: SettingsService,
    private _snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loading = true;
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;
        if (!this.userInfo.admin) {
          this._snackBar.open('Admin access required', 'Close');
          return;
        }
        this.refreshAll(() => { this.loading = false; });
      },
      error: (err: DataError) => {
        if (err.statusCode !== 401) {
          this.displayError(err.message);
        }
        this.loading = false;
      }
    });
  }

  refreshAll(always?: Function): void {
    this.dataService.getPlaatoKegDevices().subscribe({
      next: (devices: PlaatoKegDevice[]) => {
        this.devices = devices.map(d => new PlaatoKegDevice(d));
        this.filter();
        if (always) always();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if (always) always();
      }
    });
  }

  refresh(): void {
    this.loading = true;
    this.refreshAll(() => { this.loading = false; });
  }

  refreshModifyDevice(): void {
    this.loading = true;
    this._refreshModifyDevice(() => {
      this.loading = false;
    })
  }

  _refreshModifyDevice(next?: Function): void {
    if(isNilOrEmpty(this.modifyDevice)){
      return;
    }

    this.dataService.getPlaatoKegDevice(this.modifyDevice.id).subscribe({
      next: (device: PlaatoKegDevice) => {
        this.modifyDevice = new PlaatoKegDevice(device);
        this.modifyDevice.enableEditing();
        if (next) next();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if (next) next();
      }
    });
  }

  edit(device: PlaatoKegDevice): void {
    this.loading = true;
    this.modifyDevice = device;
    this._refreshModifyDevice(() => {
      this.editing = true;
      this.modifyFormGroup.reset();
      this.loading = false;
    });
  }

  save(): void {
    this.processing = true;
    this.dataService.updatePlaatoKegDevice(this.modifyDevice.id, {name: this.modifyDevice.editValues.name}).subscribe({
      next: (resp: any) => {
        this._refreshModifyDevice(() => {
          this.processing = false;
        });
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  delete(device: PlaatoKegDevice) {
    if(confirm(`Are you sure you want to delete plaato device ${device.id} (${device.name})?`)) {
      this.processing = true;
      this.dataService.deletePlaatoKegDevice(device.id).subscribe({
        next: (resp: any) => {
          this.loading = true;
          this.processing = false;
          this.refreshAll(()=>{this.loading = false});
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      }); 
    }
  }

  cancelEdit(): void {
    this.modifyDevice.disableEditing();
    this.editing = false;
  }

  displayError(errMsg: string): void {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  filter(sort?: Sort): void {
    let sortBy = 'id';
    let asc = true;

    if (sort && this.sort.active && this.sort.direction) {
      sortBy = this.sort.active;
      asc = this.sort.direction === 'asc';
    }

    let filtered = _.sortBy(this.devices, [sortBy]);
    if (!asc) _.reverse(filtered);

    this.filteredDevices = filtered;
  }

  isConnected(dev: PlaatoKegDevice): boolean {
    if (isNilOrEmpty(dev.connected)) {
      return false;
    }
    return dev.connected;
  }

  disableDeviceConfigButtons() {
    return this.processing || this.processingModeChange || this.processingSetEmptyKegWeight || this.processingSetMaxKegVolume || this.processingUnitModeChange || this.processingUnitTypeChange;
  }

  setMode(dev: PlaatoKegDevice): void {
    this.processingModeChange = true;
    this.dataService.setPlaatoKegMode(dev.id, dev.editValues.mode).subscribe({
      next: (_: any) => {
        setTimeout(() => {
          this._refreshModifyDevice(() => {
            this.processingModeChange = false
          })
        }, 3000);
      },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processingModeChange = false
        }
    });
  }

  setUnitType(dev: PlaatoKegDevice): void {
    this.processingUnitTypeChange = true;
    this.dataService.setPlaatoKegUnitType(dev.id, dev.editValues.unitType).subscribe({
      next: (_: any) => {
        setTimeout(() => {
          this._refreshModifyDevice(() => {
            this.processingUnitTypeChange = false
          })
        }, 3000);
      },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processingUnitTypeChange = false
        }
    });
  }

  setUnitMode(dev: PlaatoKegDevice): void {
    this.processingUnitModeChange = true;
    this.dataService.setPlaatoKegUnitMode(dev.id, dev.editValues.unitMode).subscribe({
      next: (_: any) => {
        setTimeout(() => {
          this._refreshModifyDevice(() => {
            this.processingUnitModeChange = false
          })
        }, 3000);
      },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processingUnitModeChange = false
        }
    });
  }

  setEmptyKegWeight(dev: PlaatoKegDevice): void {
    this.processingSetEmptyKegWeight = true;
    this.dataService.setPlaatoKegValue(dev.id, "empty_keg_weight", dev.editValues.emptyKegWeight).subscribe({
      next: (_: any) => {
        setTimeout(() => {
          this._refreshModifyDevice(() => {
            this.processingSetEmptyKegWeight = false
          })
        }, 3000);
      },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processingSetEmptyKegWeight = false
        }
    });
  }

  setMaxKegVolume(dev: PlaatoKegDevice): void {
    this.processingSetMaxKegVolume = true;
    this.dataService.setPlaatoKegValue(dev.id, "max_keg_volume", dev.editValues.maxKegVolume).subscribe({
      next: (_: any) => {
        setTimeout(() => {
          this._refreshModifyDevice(() => {
            this.processingSetMaxKegVolume = false
          })
        }, 3000);
      },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processingSetMaxKegVolume = false
        }
    });
  }

  startSetup(): void {
    this.startDeviceSetup(new PlaatoKegDevice);
  }

  startDeviceSetup(dev: PlaatoKegDevice): void {
    this.setupMode = true;
    this.setupDevice = dev;
    this.processingNewDevice = false;
    this.processingDeviceConfig = false;
    this.deviceConnectionVerified = false
    this.setupFormGroup.reset();
    this.deviceConfig = {ssid: '', pass: ''};
    this.configureDeviceFormGroup.reset();
    this.showWifiPassword = false;
  }

  cancelSetup(): void {
    this.setupMode = false;
    this.resetSetup();
    this.refresh();
  }

  resetSetup(): void {
    this.setupDevice = new PlaatoKegDevice();
    this.deviceConfig = {}
    this.setupFormGroup.reset();
    this.configureDeviceFormGroup.reset();
  }

  toggleWifiPassword(): void {
    this.showWifiPassword = !this.showWifiPassword;
  }

  createDevice(): void {
    if (!this.setupFormGroup.valid) {
      this._snackBar.open('Please fill in all required fields', 'Close');
      return;
    }

    this.processingNewDevice = true;
    const deviceData = {
      name: this.setupFormGroup.value.name
    };

    this.dataService.createPlaatoKegDevice(deviceData).subscribe({
      next: (dev: PlaatoKegDevice) => {
        this._snackBar.open(
          'Device created successfully.',
          'Close',
          { duration: 5000 }
        );
        this.setupDevice = new PlaatoKegDevice(dev);
        this.processingNewDevice = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processingNewDevice = false;
      }
    });
  }

  completeSetup(): void {
    if (!this.configureDeviceFormGroup.valid) {
      this._snackBar.open('Please fill in all required fields', 'Close');
      return;
    }

    this.processingDeviceConfig = true;
    this.textNewDevCounter = 0;

    // Get host and port from settings
    const host = encodeURIComponent(
      this.settingsService.getSetting<string>('plaato_keg_devices.config.host') || 'localhost'
    );
    const port = this.settingsService.getSetting<number>('plaato_keg_devices.config.port') || 5001;

    var ssid = encodeURIComponent(this.deviceConfig.ssid);
    var pass = encodeURIComponent(this.deviceConfig.pass);
    var id = encodeURIComponent(this.setupDevice.id);
    const url = `http://192.168.4.1/config?ssid=${ssid}&pass=${pass}&blynk=${id}&host=${host}&port=${port}`
    console.log(url);
    console.log(encodeURI(url));
    var popupRef = window.open(url);
    setTimeout(() => {
        this.checkNewDev(popupRef);
        }, 500);
  }

  checkNewDev(popupRef: Window | null) {
    this.dataService.getPlaatoKegDevice(this.setupDevice.id).subscribe({
      next: (_dev: PlaatoKegDevice) => {
        let dev = new PlaatoKegDevice(_dev);
        if (isNilOrEmpty(dev.connected) || !dev.connected) {
          this.textNewDevCounter = this.textNewDevCounter + 1;
          if(this.textNewDevCounter > 10) {
            this.displayError("Timeout trying to validate if the device was configured and connected correctly.")
            popupRef?.close();
            this.processingDeviceConfig = false;
          } else {
            setTimeout(() => {
              this.checkNewDev(popupRef);
            }, 2000)
          }
        } else {
          this._snackBar.open('Device configured successfully.', 'Close', { duration: 5000 });
          popupRef?.close();
          this.processingDeviceConfig = false;
          this.setupMode = false;
          this.resetSetup();
          this.refreshAll();
        }
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processingDeviceConfig = false;
      }
    })
  }
}
