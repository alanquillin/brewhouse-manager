import { Component, OnInit, ViewChild } from '@angular/core';
import { AbstractControl, UntypedFormControl, UntypedFormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort } from '@angular/material/sort';
import { Router } from '@angular/router';
import { CurrentUserService } from '../../_services/current-user.service';
import { DataError, DataService } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';

import { KegtronResetDialogComponent } from '../../_dialogs/kegtron-reset-dialog/kegtron-reset-dialog.component';

import { Batch, Beer, Beverage, Location, Tap, TapMonitor, UserInfo } from '../../models/models';

import * as _ from 'lodash';
import { isNilOrEmpty } from 'src/app/utils/helpers';

@Component({
  selector: 'app-taps',
  templateUrl: './taps.component.html',
  styleUrls: ['./taps.component.scss'],
  standalone: false,
})
export class ManageTapsComponent implements OnInit {
  taps: Tap[] = [];
  filteredTaps: Tap[] = [];
  locations: Location[] = [];
  beers: Beer[] = [];
  tapMonitors: TapMonitor[] = [];
  beverages: Beverage[] = [];
  batches: Batch[] = [];
  loading = false;
  processing = false;
  adding = false;
  editing = false;
  modifyTap: Tap = new Tap();
  _ = _;
  selectedLocationFilters: string[] = [];
  isNilOrEmpty = isNilOrEmpty;

  userInfo!: UserInfo;

  modifyFormGroup: UntypedFormGroup = new UntypedFormGroup({
    displayName: new UntypedFormControl('', []),
    description: new UntypedFormControl('', [Validators.required]),
    locationId: new UntypedFormControl('', [Validators.required]),
    beerBatchId: new UntypedFormControl(''),
    tapNumber: new UntypedFormControl('', [Validators.required, Validators.pattern('^[0-9]*$')]),
    tapMonitorId: new UntypedFormControl(''),
    beverageBatchId: new UntypedFormControl(''),
    namePrefix: new UntypedFormControl('', []),
    nameSuffix: new UntypedFormControl('', []),
  });

  get displayedColumns() {
    const cols = ['displayName', 'description', 'tapNumber'];

    if (this.locations.length > 1) {
      cols.push('location');
    }

    return _.concat(cols, ['beer', 'beverage', 'tapMonitor', 'actions']);
  }

  constructor(
    private currentUserService: CurrentUserService,
    private dataService: DataService,
    private settingsService: SettingsService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  refresh(always?: () => void, next?: () => void, error?: (err: DataError) => void) {
    this.dataService.getTaps().subscribe({
      next: (taps: Tap[]) => {
        this.taps = [];
        _.forEach(taps, tap => {
          const _tap = new Tap(tap);
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

          if (!isNilOrEmpty(_tap.batchId)) {
            _tap.batch = this.findBatch(_tap.batchId);
          }

          this.taps.push(_tap);
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

  _refreshAll(always?: () => void, next?: () => void, error?: (err: DataError) => void) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = _.sortBy(locations, [
          (l: Location) => {
            return l.description;
          },
        ]);
        this.dataService.getBeers().subscribe({
          next: (beers: Beer[]) => {
            this.beers = [];
            _.forEach(beers, beer => {
              this.beers.push(new Beer(beer));
            });
            this.beers = _.sortBy(this.beers, beer => {
              return beer.getName();
            });
            this.dataService.getTapMonitors().subscribe({
              next: (tapMonitors: TapMonitor[]) => {
                this.tapMonitors = tapMonitors;
                this.dataService.getBeverages().subscribe({
                  next: (beverages: Beverage[]) => {
                    this.beverages = [];
                    _.forEach(_.sortBy(beverages, ['name']), beverage => {
                      this.beverages.push(new Beverage(beverage));
                    });
                    this.dataService.getBatches().subscribe({
                      next: (batches: Batch[]) => {
                        this.batches = [];
                        _.forEach(batches, batch => {
                          const b = new Batch(batch);
                          if (isNilOrEmpty(b.beer) && !isNilOrEmpty(b.beerId)) {
                            b.beer = this.findBeer(b.beerId);
                          }
                          if (isNilOrEmpty(b.beverage) && !isNilOrEmpty(b.beverageId)) {
                            b.beverage = this.findBeverage(b.beverageId);
                          }
                          this.batches.push(b);
                        });

                        this.refresh(always, next, error);
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
        this._refreshAll(() => {
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

  refreshAll(): void {
    this.loading = true;
    this._refreshAll(() => {
      this.loading = false;
    });
  }

  add(): void {
    this.modifyFormGroup.reset();
    const data: any = {};
    if (this.locations.length === 1) {
      data['locationId'] = this.locations[0].id;
    }
    this.modifyTap = new Tap(data);
    this.modifyTap.editValues = data;
    this.adding = true;
  }

  create(): void {
    const data: any = {
      description: this.modifyTap.editValues.description,
      tapNumber: this.modifyTap.editValues.tapNumber,
      locationId: this.modifyTap.editValues.locationId,
      namePrefix: this.modifyTap.editValues.namePrefix,
      nameSuffix: this.modifyTap.editValues.nameSuffix,
    };

    if (!_.isNil(this.modifyTap.editValues.beerId) && this.modifyTap.editValues.beerId !== '-1') {
      data['beerId'] = this.modifyTap.editValues.beerId;
    }

    if (
      !_.isNil(this.modifyTap.editValues.tapMonitorId) &&
      this.modifyTap.editValues.tapMonitorId !== '-1'
    ) {
      data['tapMonitorId'] = this.modifyTap.editValues.tapMonitorId;
    }

    if (
      !_.isNil(this.modifyTap.editValues.beverageId) &&
      this.modifyTap.editValues.beverageId !== '-1'
    ) {
      data['beverageId'] = this.modifyTap.editValues.beverageId;
    }

    this.processing = true;
    this.dataService.createTap(data).subscribe({
      next: (_: Tap) => {
        this.refresh(
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

  edit(tap: Tap): void {
    tap.enableEditing();
    this.modifyTap = tap;
    this.editing = true;
    this.modifyFormGroup.reset();
  }

  save(): void {
    const updateData: any = _.cloneDeep(this.modifyTap.changes);

    if (
      _.has(updateData, 'batchId') &&
      (updateData.batchId === '-1' || _.isNil(updateData.batchId))
    ) {
      updateData.batchId = null;
    }

    if (
      _.has(updateData, 'tapMonitorId') &&
      (updateData.tapMonitorId === '-1' || _.isNil(updateData.tapMonitorId))
    ) {
      updateData.tapMonitorId = null;
    }

    if (_.has(updateData, 'batchId') && this.modifyTap.tapMonitor?.monitorType === 'kegtron-pro') {
      const batch = updateData.batchId ? this.findBatch(updateData.batchId) : undefined;
      const dialogRef = this.dialog.open(KegtronResetDialogComponent, {
        data: {
          deviceId: this.modifyTap.tapMonitor.meta.deviceId,
          portNum: this.modifyTap.tapMonitor.meta.portNum,
          showSkip: true,
          updateDateTapped: true,
          batchId: batch?.id,
        },
      });
      dialogRef.afterClosed().subscribe(result => {
        if (result === 'submit' || result === 'skip') {
          this._executeSave(updateData);
        }
      });
    } else {
      this._executeSave(updateData);
    }
  }

  private _executeSave(updateData: any): void {
    this.processing = true;
    this.dataService.updateTap(this.modifyTap.id, updateData).subscribe({
      next: (_: Tap) => {
        this.modifyTap.disableEditing();
        this.refresh(
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
    this.modifyTap.disableEditing();
    this.editing = false;
  }

  delete(tap: Tap): void {
    if (
      confirm(
        `Are you sure you want to delete tap #${tap.tapNumber} (${tap.description}) from '${_.isNil(tap.location) ? 'UNKNOWN' : tap.location.name}'?`
      )
    ) {
      this.processing = true;
      this.dataService.deleteTap(tap.id).subscribe({
        next: (_: any) => {
          this.processing = false;
          this.loading = true;
          this.refresh(() => {
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

  filter(sort?: Sort): void {
    let sortBy = 'tapNumber';
    let asc = true;
    if (!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    let filteredData: Tap[] = this.taps;
    if (!_.isEmpty(this.selectedLocationFilters)) {
      filteredData = _.filter(this.taps, s => {
        return this.selectedLocationFilters.includes(s.locationId);
      }) as Tap[];
    }

    filteredData = _.sortBy(filteredData, [
      (d: Tap) => {
        if (sortBy === 'location') {
          return _.isNil(d.location) ? '' : d.location.name;
        }
        if (sortBy === 'tapMonitor') {
          return _.isNil(d.tapMonitor) ? '' : d.tapMonitor.name;
        }
        if (sortBy === 'beer') {
          return _.isNil(d.beer) ? '' : d.beer.getName();
        }
        return _.get(d, sortBy);
      },
    ]);
    if (!asc) {
      _.reverse(filteredData);
    }
    this.filteredTaps = filteredData;
  }

  getTapMonitorName(tapMonitor: TapMonitor | undefined, tapMonitorId?: string): string {
    if (_.isNil(tapMonitor) && !_.isNil(tapMonitorId)) {
      tapMonitor = _.find(this.tapMonitors, s => {
        return s.id === tapMonitorId;
      });
    }
    if (_.isNil(tapMonitor)) {
      return '';
    }
    let name = tapMonitor.name;
    if (_.isEmpty(name)) {
      name = 'UNNAMED';
    }
    return `${name} (${tapMonitor.monitorType})`;
  }

  findBeer(beerId: string) {
    return _.find(this.beers, b => {
      return b.id == beerId;
    });
  }

  findBeverage(beverageId: string) {
    return _.find(this.beverages, b => {
      return b.id == beverageId;
    });
  }

  findBatch(batchId: string) {
    return _.find(this.batches, b => {
      return b.id == batchId;
    });
  }

  getTapMonitorsForLocation(locationId: string | undefined): TapMonitor[] {
    if (_.isNil(locationId)) {
      return [];
    }

    const tapMonitors = _.filter(this.tapMonitors, s => {
      return s.locationId === locationId;
    });
    if (_.isNil(tapMonitors)) {
      return [];
    }
    return tapMonitors;
  }

  get modifyForm(): Record<string, AbstractControl> {
    return this.modifyFormGroup.controls;
  }

  showDisplayNameToolTip(tap: Tap) {
    return !isNilOrEmpty(tap.namePrefix) || !isNilOrEmpty(tap.nameSuffix);
  }

  clear(tap: Tap) {
    if (confirm(`Are you sure you want to clear the tap?`)) {
      this.processing = true;
      this.dataService.clearTap(tap.id).subscribe({
        next: (_: any) => {
          this.processing = false;
          this.loading = true;
          this.refresh(() => {
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

  getBeerBatches(locationId: string): Batch[] {
    const b: Batch[] = [];
    _.forEach(this.batches, batch => {
      if (!isNilOrEmpty(batch.beerId) && !isNilOrEmpty(batch.beer)) {
        if (batch?.locationIds.includes(locationId)) {
          b.push(batch);
        }
      }
    });

    return b;
  }

  getBeverageBatches(locationId: string): Batch[] {
    const b: Batch[] = [];
    _.forEach(this.batches, batch => {
      if (!isNilOrEmpty(batch.beverageId) && !isNilOrEmpty(batch.beverage)) {
        if (batch?.locationIds.includes(locationId)) {
          b.push(batch);
        }
      }
    });

    return b;
  }

  getBeerBatchName(batch?: Batch): string {
    if (isNilOrEmpty(batch)) {
      return '';
    }

    if (isNilOrEmpty(batch?.beer)) {
      return '';
    }

    return this.getBatchDisplayName(batch);
  }

  getBeverageBatchName(batch?: Batch): string {
    if (isNilOrEmpty(batch)) {
      return '';
    }

    if (isNilOrEmpty(batch?.beverage)) {
      return '';
    }

    return this.getBatchDisplayName(batch);
  }

  getBatchDisplayName(batch?: Batch): string {
    if (isNilOrEmpty(batch)) {
      return '';
    }

    let name: string | undefined = '';

    if (!isNilOrEmpty(batch?.beer)) {
      name = batch?.getName();
      if (isNilOrEmpty(name)) {
        name = batch?.beer?.getName();
      }
    }
    if (!isNilOrEmpty(batch?.beverage)) {
      name = batch?.name;
      if (isNilOrEmpty(name)) {
        name = batch?.beverage?.name;
      }
    }

    if (isNilOrEmpty(name)) {
      return '';
    }

    name = `${name} (batch #${batch?.getBatchNumber()})`;

    return name;
  }
}
