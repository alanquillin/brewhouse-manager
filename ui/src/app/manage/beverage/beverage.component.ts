import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { FormControl, AbstractControl, Validators, FormGroup } from '@angular/forms';

import { FileUploadDialogComponent } from '../../_dialogs/file-upload-dialog/file-upload-dialog.component';
import { ImageSelectorDialogComponent } from '../../_dialogs/image-selector-dialog/image-selector-dialog.component'
import { LocationImageDialog } from '../../_dialogs/image-preview-dialog/image-preview-dialog.component'

import { Beverage, Settings } from '../../models/models';
import { isNilOrEmpty } from '../../utils/helpers';
import { toUnixTimestamp } from '../../utils/datetime';

import * as _ from 'lodash';

@Component({
  selector: 'app-beverages',
  templateUrl: './beverage.component.html',
  styleUrls: ['./beverage.component.scss']
})
export class ManageBeverageComponent implements OnInit {

  loading = false;
  beverages: Beverage[] = [];
  filteredBeverages: Beverage[] = [];
  processing = false;
  adding = false;
  editing = false;
  modifyBeverage: Beverage = new Beverage();
  isNilOrEmpty: Function = isNilOrEmpty;
  defaultType!: string;
  supportedTypes: string[] = [];
  _ = _;

  modifyFormGroup: FormGroup = new FormGroup({
    name: new FormControl('', [Validators.required]),
    type: new FormControl('', [Validators.required]),
    description: new FormControl('', []),
    brewery: new FormControl('', []),
    breweryLink: new FormControl('', []),
    flavor: new FormControl('', []),
    brewDate: new FormControl(new Date(), []),
    kegDate: new FormControl(new Date(), []),
    imgUrl: new FormControl('', []),
    roastery: new FormControl('', []),
    roasteryLink: new FormControl('', []),
  });

  get displayedColumns(): string[] {
    return ["name", "description", "type", "brewery", "roastery", "flavor", "kegDate", "brewDate", "imgUrl", "actions"];
  }

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar, public dialog: MatDialog) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getSettings().subscribe({
      next: (data: Settings) => {
        this.defaultType = data.beverages.defaultType;
        this.supportedTypes = data.beverages.supportedTypes;

        this.dataService.getBeverages().subscribe({
          next: (beverages: Beverage[]) => {
            this.beverages = [];
            _.forEach(beverages, (beverage) => {
              var _beverage = new Beverage(beverage)
              this.beverages.push(_beverage)
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
        });
      },
      error: (err: DataError) => {
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
    this.refresh(()=> {
      this.loading = false;
    })
  }

  add(): void {
    this.modifyFormGroup.reset();
    var data: any = {type: this.defaultType, meta: {}}

    this.modifyBeverage = new Beverage(data);
    this.modifyBeverage.editValues = data;
    this.adding = true;
  }

  dateToNumber(v: any) : number | undefined {
    return isNilOrEmpty(v) ? undefined : _.isDate(v) ? toUnixTimestamp(v) : _.toNumber(v);
  }

  create(): void {
    this.processing = true;
    var data: any = {
      name: this.modifyBeverage.editValues.name,
      description: this.modifyBeverage.editValues.description,
      type: this.modifyBeverage.editValues.type,
      brewery: this.modifyBeverage.editValues.brewery,
      breweryLink: this.modifyBeverage.editValues.breweryLink,
      flavor: this.modifyBeverage.editValues.flavor,
      imgUrl: this.modifyBeverage.editValues.imgUrl,
      brewDate: this.dateToNumber(this.modifyBeverage.editValues.brewDateObj),
      kegDate: this.dateToNumber(this.modifyBeverage.editValues.kegDateObj),
      meta: this.modifyBeverage.editValues.meta
    }
    console.log(data);
    this.dataService.createBeverage(data).subscribe({
      next: (beverage: Beverage) => {
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

  edit(beverage: Beverage): void {
    beverage.enableEditing();
    this.modifyBeverage = beverage;
    this.editing = true;
    this.modifyFormGroup.reset();
  }

  save(): void {
    this.processing = true;
    this.dataService.updateBeverage(this.modifyBeverage.id, this.modifyBeverage.changes).subscribe({
      next: (beverage: Beverage) => {
        this.modifyBeverage.disableEditing();
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
    this.modifyBeverage.disableEditing();
    this.editing = false;
  }

  delete(beverage: Beverage): void {
    if(confirm(`Are you sure you want to delete beverage '${beverage.name}'?`)) {
      this.processing = true;
      this.dataService.deleteBeverage(beverage.id).subscribe({
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

  filter(sort?: Sort) {
    var sortBy:string = "description";
    var asc: boolean = true;

    if(!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    var filteredData: Beverage[] = this.beverages;
    
    filteredData = _.sortBy(filteredData, [(d: Beverage) => {
        return _.get(d, sortBy);
      }]);
    if(!asc){
      _.reverse(filteredData);
    }
    this.filteredBeverages = filteredData;
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  }

  openUploadDialog(): void {
    const dialogRef = this.dialog.open(FileUploadDialogComponent, {
      data: {
        imageType: "beverage"
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        const f = result[0];
        this.modifyBeverage.editValues.imgUrl = f.path;
      }
    });
  }

  openImageSelectorDialog(): void {
    const dialogRef = this.dialog.open(ImageSelectorDialogComponent, {
      width: '1200px',
      data: {
        imageType: "beverage"
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        this.modifyBeverage.editValues.imgUrl = result;
      }
    });
  }

  openImagePreviewDialog(imgUrl: string): void {
    this.dialog.open(LocationImageDialog, {
      data: {
        imgUrl: imgUrl,
      },
    });
  }
}
