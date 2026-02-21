import { Component, OnInit, ViewChild } from '@angular/core';
import { AbstractControl, UntypedFormControl, UntypedFormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort } from '@angular/material/sort';
import { Router } from '@angular/router';
import { CurrentUserService } from '../../_services/current-user.service';
import { DataError, DataService } from '../../_services/data.service';

import { KegtronResetDialogComponent } from '../../_dialogs/kegtron-reset-dialog/kegtron-reset-dialog.component';

import {
  Location,
  TapMonitor,
  TapMonitorDiscoveryData,
  TapMonitorType,
  UserInfo,
} from '../../models/models';

import { isNilOrEmpty } from '../../utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-tap-monitors',
  templateUrl: './tap-monitors.component.html',
  styleUrls: ['./tap-monitors.component.scss'],
  standalone: false,
})
export class ManageTapMonitorsComponent implements OnInit {
  loading = false;
  tapMonitors: TapMonitor[] = [];
  filteredTapMonitors: TapMonitor[] = [];
  locations: Location[] = [];
  monitorTypes: TapMonitorType[] = [];
  processing = false;
  adding = false;
  editing = false;
  modifyTapMonitor: TapMonitor = new TapMonitor();
  _ = _;
  selectedLocationFilters: string[] = [];
  tapMonitorDiscoveryData: TapMonitorDiscoveryData[] = [];
  tapMonitorDiscoveryProcessing = false;
  selectedDiscoveredTapMonitorId: any;

  userInfo!: UserInfo;

  modifyFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [Validators.required]),
    monitorType: new UntypedFormControl('', [Validators.required]),
    locationId: new UntypedFormControl('', [Validators.required]),
    metaAuthToken: new UntypedFormControl('', []),
    kvmDevice: new UntypedFormControl('', []),
    opkDevice: new UntypedFormControl('', []),
  });

  allowedMassUnits = ['g', 'kg', 'oz', 'lb'];
  allowedLiquidUnits = ['ml', 'l', 'gal'];

  get displayedColumns(): string[] {
    const cols = ['name', 'type'];

    if (this.locations.length > 1) {
      cols.push('location');
    }

    return _.concat(cols, ['tap', 'actions']);
  }

  constructor(
    private currentUserService: CurrentUserService,
    private dataService: DataService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  _refresh(always?: () => void, next?: () => void, error?: (err: DataError) => void) {
    this.dataService.getTapMonitors(undefined, true).subscribe({
      next: (tapMonitors: TapMonitor[]) => {
        this.tapMonitors = [];
        _.forEach(tapMonitors, tapMonitor => {
          const _tapMonitor = new TapMonitor(tapMonitor);
          this.tapMonitors.push(_tapMonitor);
        });
        this.filter();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if (!_.isNil(error)) {
          error(err);
        }
        if (!_.isNil(always)) {
          always();
        }
      },
      complete: () => {
        if (!_.isNil(next)) {
          next();
        }
        if (!_.isNil(always)) {
          always();
        }
      },
    });
  }

  refreshAll(always?: () => void, next?: () => void, error?: (err: DataError) => void) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = _.sortBy(locations, [
          (l: Location) => {
            return l.description;
          },
        ]);
        this.dataService.getMonitorTypes().subscribe({
          next: (monitorTypes: TapMonitorType[]) => {
            this.monitorTypes = _.orderBy(monitorTypes, ['type']);
            this._refresh(always, next, error);
          },
          error: (err: DataError) => {
            this.displayError(err.message);
            if (!_.isNil(error)) {
              error(err);
            }
            if (!_.isNil(always)) {
              always();
            }
          },
        });
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if (!_.isNil(error)) {
          error(err);
        }
        if (!_.isNil(always)) {
          always();
        }
      },
    });
  }

  ngOnInit(): void {
    this.loading = true;
    this.currentUserService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo | null) => {
        this.userInfo = userInfo!;

        if (this.userInfo?.locations && this.userInfo?.admin) {
          for (const l of this.userInfo.locations) {
            this.selectedLocationFilters.push(l.id);
          }
        }
        this.refreshAll(() => {
          this.loading = false;
        });
      },
      error: (err: DataError) => {
        if (err.statusCode !== 401) {
          this.displayError(err.message);
        }
      },
    });
  }

  refresh(): void {
    this.loading = true;
    this.refreshAll(() => {
      this.loading = false;
    });
  }

  add(): void {
    this.modifyFormGroup.reset();
    const data: any = { meta: {} };
    if (this.locations.length === 1) {
      data['locationId'] = this.locations[0].id;
    }
    if (this.monitorTypes.length === 1) {
      data['monitorType'] = this.monitorTypes[0].type;
    }

    this.modifyTapMonitor = new TapMonitor(data);
    this.modifyTapMonitor.editValues = data;
    if (!isNilOrEmpty(data['monitorType']) && this.currentTypeSupportsDiscovery()) {
      this.discoverTapMonitors();
    }
    this.adding = true;
  }

  create(): void {
    this.processing = true;
    const meta: any = {};
    if (this.modifyTapMonitor.editValues.monitorType == 'plaato-blynk') {
      meta.authToken = this.modifyTapMonitor.editValues.meta.authToken;
    }

    if (
      [
        'keg-volume-monitor-weight',
        'keg-volume-monitor-flow',
        'kegtron-pro',
        'open-plaato-keg',
        'plaato-keg',
      ].includes(this.modifyTapMonitor.editValues.monitorType)
    ) {
      meta.deviceId = this.modifyTapMonitor.editValues.meta.deviceId;
    }

    if (this.modifyTapMonitor.editValues.monitorType == 'kegtron-pro') {
      meta.deviceId = this.modifyTapMonitor.editValues.meta.deviceId;
      meta.portNum = _.toInteger(this.modifyTapMonitor.editValues.meta.portNum);
      meta.accessToken = this.modifyTapMonitor.editValues.meta.accessToken;
    }

    const data: any = {
      name: this.modifyTapMonitor.editValues.name,
      monitorType: this.modifyTapMonitor.editValues.monitorType,
      locationId: this.modifyTapMonitor.editValues.locationId,
      meta: meta,
    };
    this.dataService.createTapMonitor(data).subscribe({
      next: (_: TapMonitor) => {
        this._refresh(
          () => {
            this.processing = false;
          },
          () => {
            this.adding = false;
          }
        );
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      },
    });
  }

  cancelAdd(): void {
    this.adding = false;
  }

  edit(tapMonitor: TapMonitor): void {
    tapMonitor.enableEditing();
    this.modifyTapMonitor = tapMonitor;
    this.editing = true;
    this.modifyFormGroup.reset();
    if (this.currentTypeSupportsDiscovery()) {
      this.discoverTapMonitors(() => {
        if (!isNilOrEmpty(this.modifyTapMonitor.editValues.meta)) {
          if (
            this.modifyTapMonitor.editValues.monitorType == 'keg-volume-monitor-weight' ||
            this.modifyTapMonitor.editValues.monitorType == 'keg-volume-monitor-flow'
          ) {
            this.selectedDiscoveredTapMonitorId = _.get(
              this.modifyTapMonitor.editValues.meta,
              'deviceId'
            );
          } else if (this.modifyTapMonitor.editValues.monitorType == 'kegtron-pro') {
            const deviceId = _.get(this.modifyTapMonitor.editValues.meta, 'deviceId');
            const portNum = _.get(this.modifyTapMonitor.editValues.meta, 'portNum');
            this.selectedDiscoveredTapMonitorId = deviceId + '|' + portNum;
          } else if (this.modifyTapMonitor.editValues.monitorType == 'open-plaato-keg') {
            this.selectedDiscoveredTapMonitorId = _.get(
              this.modifyTapMonitor.editValues.meta,
              'deviceId'
            );
          }
        }
      });
    }
  }

  save(): void {
    this.processing = true;
    this.dataService
      .updateTapMonitor(this.modifyTapMonitor.id, this.modifyTapMonitor.changes)
      .subscribe({
        next: (_: any) => {
          this.modifyTapMonitor.disableEditing();
          this._refresh(
            () => {
              this.processing = false;
            },
            () => {
              this.editing = false;
            }
          );
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        },
      });
  }

  cancelEdit(): void {
    this.modifyTapMonitor.disableEditing();
    this.editing = false;
  }

  delete(tapMonitor: TapMonitor): void {
    if (confirm(`Are you sure you want to delete tap monitor '${tapMonitor.name}'?`)) {
      this.processing = true;
      this.dataService.deleteTapMonitor(tapMonitor.id).subscribe({
        next: (_: any) => {
          this.processing = false;
          this.loading = true;
          this._refresh(() => {
            this.loading = false;
          });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        },
      });
    }
  }

  getLocationName(tapMonitor: TapMonitor): string {
    const loc = _.find(this.locations, l => {
      return l.id === tapMonitor.locationId;
    });

    if (_.isNil(loc) || _.isEmpty(loc)) {
      return 'UNKNOWN';
    }

    return (loc as Location).name;
  }

  filter(sort?: Sort) {
    let sortBy = 'description';
    let asc = true;

    if (!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    let filteredData: TapMonitor[] = this.tapMonitors;
    if (!_.isEmpty(this.selectedLocationFilters)) {
      filteredData = _.filter(this.tapMonitors, s => {
        return this.selectedLocationFilters.includes(s.locationId);
      }) as TapMonitor[];
    }

    filteredData = _.sortBy(filteredData, [
      (d: TapMonitor) => {
        if (sortBy === 'location') {
          return _.isNil(d.location) ? '' : d.location.name;
        }
        return _.get(d, sortBy);
      },
    ]);
    if (!asc) {
      _.reverse(filteredData);
    }
    this.filteredTapMonitors = filteredData;
  }

  getMonitorType(type: string): TapMonitorType | undefined {
    return _.find(this.monitorTypes, mt => mt.type === type);
  }

  currentTypeSupportsDiscovery(): boolean {
    const monitorType = this.getMonitorType(this.modifyTapMonitor.editValues.monitorType);
    return monitorType?.supportsDiscovery ?? false;
  }

  monitorTypeChanged() {
    if (this.currentTypeSupportsDiscovery()) {
      this.discoverTapMonitors();
    }
  }

  discoverTapMonitors(next?: () => void) {
    this.tapMonitorDiscoveryData = [];
    this.tapMonitorDiscoveryProcessing = true;
    this.dataService.discoverTapMonitors(this.modifyTapMonitor.editValues.monitorType).subscribe({
      next: (data: TapMonitorDiscoveryData[]) => {
        this.tapMonitorDiscoveryData = data;
        if (!_.isNil(next)) {
          next();
        }
        this.tapMonitorDiscoveryProcessing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.tapMonitorDiscoveryProcessing = false;
      },
    });
  }

  selectedDiscoveredTapMonitorChange() {
    if (
      [
        'keg-volume-monitor-weight',
        'keg-volume-monitor-flow',
        'open-plaato-keg',
        'plaato-keg',
      ].includes(this.modifyTapMonitor.editValues.monitorType)
    ) {
      this.modifyTapMonitor.editValues.meta.deviceId = this.selectedDiscoveredTapMonitorId;
    }

    if (this.modifyTapMonitor.editValues.monitorType == 'kegtron-pro') {
      const parts = _.split(this.selectedDiscoveredTapMonitorId, '|');
      this.modifyTapMonitor.editValues.meta.deviceId = parts[0];
      this.modifyTapMonitor.editValues.meta.portNum = _.toInteger(parts[1]);
      _.forEach(this.tapMonitorDiscoveryData, dev => {
        if (
          dev.id === this.modifyTapMonitor.editValues.meta.deviceId &&
          dev.portNum === this.modifyTapMonitor.editValues.meta.portNum
        ) {
          this.modifyTapMonitor.editValues.meta.accessToken = dev.token;
        }
      });
    }
  }

  get modifyForm(): Record<string, AbstractControl> {
    return this.modifyFormGroup.controls;
  }

  resetKegtron(tapMonitor: TapMonitor): void {
    this.dialog.open(KegtronResetDialogComponent, {
      data: {
        deviceId: tapMonitor.meta.deviceId,
        portNum: tapMonitor.meta.portNum,
      },
    });
  }

  getTapDetails(tapMonitor: TapMonitor): string {
    if (isNilOrEmpty(tapMonitor.tap)) {
      return '';
    }

    return `Tap #${tapMonitor.tap.tapNumber} (${tapMonitor.tap.description})`;
  }
}
