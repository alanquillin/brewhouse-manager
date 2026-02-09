import { Component, OnInit } from '@angular/core';
import { AbstractControl, UntypedFormControl, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableDataSource } from '@angular/material/table';
import { Router } from '@angular/router';
import { DataError, DataService } from '../../_services/data.service';

import { Location } from '../../models/models';

import * as _ from 'lodash';

@Component({
  selector: 'app-locations',
  templateUrl: './locations.component.html',
  styleUrls: ['./locations.component.scss'],
  standalone: false,
})
export class ManageLocationsComponent implements OnInit {
  loading = false;
  locations: Location[] = [];
  displayedColumns: string[] = ['name', 'description', 'actions'];
  dataSource = new MatTableDataSource<Location>(this.locations);
  processing = false;
  adding = false;
  addLocation: Location = new Location();
  _ = _;

  nameValidationPattern = '^[a-z0-9_-]*$';

  addFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [
      Validators.required,
      Validators.pattern(this.nameValidationPattern),
    ]),
    description: new UntypedFormControl('', [Validators.required]),
  });

  nameFormControl = new UntypedFormControl('', [
    Validators.required,
    Validators.pattern(this.nameValidationPattern),
  ]);
  descriptionFormControl = new UntypedFormControl('', [Validators.required]);

  constructor(
    private dataService: DataService,
    private router: Router,
    private _snackBar: MatSnackBar
  ) {}

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  _refresh(always?: Function, next?: Function, error?: Function) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = [];
        _.forEach(
          _.sortBy(locations, [
            (l: Location) => {
              return l.description;
            },
          ]),
          location => {
            const eLoc = new Location();
            Object.assign(eLoc, location);
            this.locations.push(eLoc);
          }
        );
        this.dataSource.data = this.locations;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if (!_.isNil(error)) {
          error();
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

  ngOnInit(): void {
    this.loading = true;
    this._refresh(() => {
      this.loading = false;
    });
  }

  refresh(): void {
    this.loading = true;
    this._refresh(() => {
      this.loading = false;
    });
  }

  edit(location: Location): void {
    location.enableEditing();
  }

  delete(location: Location): void {
    if (
      confirm(
        `Are you sure you want to delete location '${location.name}'?  All associated taps and tap monitors will be deleted as well.`
      )
    ) {
      this.processing = true;
      this.dataService.deleteLocation(location.id).subscribe({
        error: (err: DataError) => {
          this.displayError(err.message);
        },
        complete: () => {
          this.processing = false;
          this.loading = true;
          this._refresh(() => {
            this.loading = false;
          });
        },
      });
    }
  }

  save(location: Location): void {
    if (_.isNil(location.changes) || _.isEmpty(location.changes)) {
      return;
    }

    this.dataService.updateLocation(location.id, location.changes).subscribe({
      next: (data: Location) => {
        Object.assign(location, data);
        location.disableEditing();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
      },
    });
  }

  cancel(location: Location): void {
    location.disableEditing();
  }

  add(): void {
    this.addLocation = new Location();
    this.adding = true;
  }

  create(): void {
    this.processing = true;
    this.dataService
      .createLocation({ name: this.addLocation.name, description: this.addLocation.description })
      .subscribe({
        next: (data: Location) => {
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
          this.processing = false;
          this.displayError(err.message);
        },
      });
  }

  cancelAdd(): void {
    this.adding = false;
  }

  get addForm(): Record<string, AbstractControl> {
    return this.addFormGroup.controls;
  }
}
