import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { FormControl, AbstractControl, ValidatorFn, ValidationErrors, Validators, FormGroup } from '@angular/forms';

import { FileUploadDialogComponent } from '../../_dialogs/file-upload-dialog/file-upload-dialog.component';
import { ImageSelectorDialogComponent } from '../../_dialogs/image-selector-dialog/image-selector-dialog.component'
import { LocationImageDialog } from '../../_dialogs/image-preview-dialog/image-preview-dialog.component'

import { Beer, beerTransformFns } from '../../models/models';
import { isNilOrEmpty } from '../../utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-beer',
  templateUrl: './beer.component.html',
  styleUrls: ['./beer.component.scss']
})
export class ManageBeerComponent implements OnInit {
  loading = false;
  beers: Beer[] = [];
  filteredBeers: Beer[] = [];
  displayedColumns: string[] = ['name', 'description', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', "untappdId", 'imgUrl', 'actions'];
  processing = false;
  adding = false;
  editing = false;
  modifyBeer: Beer = new Beer();
  isNilOrEmpty: Function = isNilOrEmpty;
  _ = _;

  transformFns = beerTransformFns;

  externalBrewingTools: string[] = ["brewfather"]

  decimalRegex = /^-?\d*[.]?\d{0,2}$/;
  decimalValidator = Validators.pattern(this.decimalRegex); 

  requiredIfNoBrewTool(comp: ManageBeerComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null  => {
      var brewTool = _.get(comp.modifyBeer.editValues, "externalBrewingTool")
      if(!_.isEmpty(brewTool) && brewTool !== "-1"){
        return null;
      }
      
      if(isNilOrEmpty(control.value)) {
        return { requiredIfNoToolSelected: true };
      }

      return null;
    }
  }
  
  requiredForBrewingTool(comp: ManageBeerComponent, tool: string): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      var brewTool = _.get(comp.modifyBeer.editValues, "externalBrewingTool")
      if(_.isEmpty(brewTool) || brewTool === "-1"){
        return null;
      }
      
      if(brewTool === tool && (_.isNil(control.value) || _.isEmpty(control.value))){
        return { requiredForBrewTool: true };
      }

      return null;
    }
  }

  modifyFormGroup: FormGroup = new FormGroup({
    name: new FormControl('', [this.requiredIfNoBrewTool(this)]),
    description: new FormControl('', [this.requiredIfNoBrewTool(this)]),
    style: new FormControl('', [this.requiredIfNoBrewTool(this)]),
    abv: new FormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    srm: new FormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    ibu: new FormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    externalBrewingTool: new FormControl(-1),
    brewDate: new FormControl(new Date(), [this.requiredIfNoBrewTool(this)]),
    kegDate: new FormControl(new Date(), [this.requiredIfNoBrewTool(this)]),
    imgUrl: new FormControl(''),
    brewfatherBatchId: new FormControl('', [this.requiredForBrewingTool(this, "brewfather")]),
    untappdId: new FormControl('')
  });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar, public dialog: MatDialog) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getBeers().subscribe({
      next: (beers: Beer[]) => {
        this.beers = [];
        _.forEach(beers, (beer) => {
          var _beer = new Beer()
          Object.assign(_beer, beer);
          this.beers.push(_beer)
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

  ngOnInit(): void {
    this.loading = true;
    this.refresh(()=> {
      this.loading = false;
    })
  }

  add(): void {
    this.modifyFormGroup.reset();
    this.modifyBeer = new Beer();
    this.adding = true;
  }

  create(): void {
    var data: any = {}
    const name = _.get(this.modifyBeer.editValues, "name");
    const keys = ['name', 'description', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', 'imgUrl', 'externalBrewingToolMeta']
    const checkKeys = {"brewDate": "brewDateObj", "kegDate": "kegDateObj"}
    
    _.forEach(keys, (k) => {
      const checkKey = _.get(checkKeys, k, k);

      var val: any = _.get(this.modifyBeer.editValues, checkKey);
      if(isNilOrEmpty(val)){
        return;
      }
      const transformFn = _.get(this.transformFns, k);
      if(!_.isNil(transformFn)){
        val = transformFn(val);
      }
      data[k] = val;
    })

    if(_.has(data, "externalBrewingTool")){
      const tool = data["externalBrewingTool"];
      if(isNilOrEmpty(tool)) {
        delete data["externalBrewingTool"];
      }
    }

    if (_.has(data, "externalBrewingToolMeta")) {
      if(isNilOrEmpty(_.get(data, "externalBrewingTool"))) {
        delete data["externalBrewingToolMeta"];
      }
    }
    
    this.processing = true;
    this.dataService.createBeer(data).subscribe({
      next: (beer: Beer) => {
        this.refresh(() => {this.processing = false;}, () => {this.adding = false;});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  cancelAdd(): void {
    this.adding = false;
  }

  edit(beer: Beer): void {
    beer.enableEditing();
    this.modifyBeer = beer;
    this.editing = true;
    this.modifyFormGroup.reset();
    this.reRunValidation();
  }

  save(): void {  
    this.processing = true;
    this.dataService.updateBeer(this.modifyBeer.id, this.changes).subscribe({
      next: (beer: Beer) => {
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
    this.modifyBeer.disableEditing();
    this.editing = false;
  }

  delete(beer: Beer): void {
    if(confirm(`Are you sure you want to delete beer '${beer.getName()}'?`)) {
      this.processing = true;
      this.dataService.deleteBeer(beer.id).subscribe({
        next: (resp: any) => {
          this.processing = false;
          this.loading = true;
          this.refresh(()=>{this.loading = false});
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

    var filteredData: Beer[] = this.beers;
    filteredData= _.sortBy(filteredData, [
      (d: Beer) => { 
        if (sortBy === "name") {
          return d.getName();
        }

        if (sortBy === "description") {
          return d.getDescription();
        }

        if (sortBy === "style") {
          return d.getStyle();
        }

        if (sortBy === "abv") {
          return d.getAbv();
        }

        if (sortBy === "ibu") {
          return d.getIbu();
        }

        if (sortBy === "kegDate") {
          return d.getKegDate();
        }

        if (sortBy === "brewDate") {
          return d.getBrewDate();
        }

        if (sortBy === "srm") {
          return d.getSrm();
        }
        return _.get(d, sortBy); 
      }]
    );
    if(!asc){
      _.reverse(filteredData);
    }
    this.filteredBeers = filteredData;
  }

  brewToolChanges(event?: any) {
    this.addMissingMeta();
    this.reRunValidation();
  }

  addMissingMeta() {
    switch(this.modifyBeer.editValues.externalBrewingTool) {
      case "brewfather":
        if(!_.has(this.modifyBeer.editValues.externalBrewingToolMeta, "batchId")){
          _.set(this.modifyBeer.editValues, 'externalBrewingToolMeta.batchId', '');
        }
        break
    }
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  } 

  reRunValidation(): void {
    _.forEach(this.modifyForm, (ctrl) => {
      ctrl.updateValueAndValidity();
    });
  }

  get hasChanges(): boolean {
    if(!this.modifyBeer.hasChanges) {
      return false;
    }

    return !_.isEmpty(this.changes)
  }

  get changes(): any {
    var changes = _.cloneDeep(this.modifyBeer.changes);

    if (_.get(changes, "externalBrewingTool") === "-1") {
      changes["externalBrewingTool"] = null;
      changes["externalBrewingToolMeta"] = null;
    } else {
      if (_.has(changes, "externalBrewingToolMeta")) {
        if(isNilOrEmpty(_.get(this.modifyBeer, "externalBrewingTool"))) {
          delete changes["externalBrewingToolMeta"];
        }
      }
    }

    if(_.has(_.get(changes, "externalBrewingToolMeta", {}), "details")) {
      delete changes["externalBrewingToolMeta"]["details"]
    }

    const keys = ['name', 'description', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', 'imgUrl']
    _.forEach(keys, (k) => {
      if(_.has(changes, k)) {
        if(isNilOrEmpty(changes[k])) {
          changes[k] = null;
        }
      }
    });
    return changes;
  }

  openUploadDialog(): void {
    const dialogRef = this.dialog.open(FileUploadDialogComponent, {
      data: {
        imageType: "beer"
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        const f = result[0];
        this.modifyBeer.editValues.imgUrl = f.path;
      }
    });
  }

  openImageSelectorDialog(): void {
    const dialogRef = this.dialog.open(ImageSelectorDialogComponent, {
      width: '1200px',
      data: {
        imageType: "beer"
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        this.modifyBeer.editValues.imgUrl = result;
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

  getBeerLink(beer: Beer) : string {
    if (_.isNil(beer))
      return "";

    var batchId = _.get(beer.externalBrewingToolMeta, "batchId");
    if (beer.externalBrewingTool === "brewfather" && beer.externalBrewingToolMeta && !isNilOrEmpty(batchId)) {
      return `https://web.brewfather.app/tabs/batches/batch/${batchId}`;
    }

    return "";
  }
}
