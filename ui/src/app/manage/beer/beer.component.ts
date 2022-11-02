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

import { Beer, beerTransformFns, ImageTransition, Location } from '../../models/models';
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
  processing = false;
  adding = false;
  editing = false;
  modifyBeer: Beer = new Beer();
  isNilOrEmpty: Function = isNilOrEmpty;
  imageTransitionsToDelete: string[] = [];
  locations: Location[] = [];
  selectedLocationFilters: string[] = [];
  _ = _;

  transformFns = beerTransformFns;

  externalBrewingTools: string[] = ["brewfather"]

  get displayedColumns() {
    var cols = ['name', 'description'];

    if(!isNilOrEmpty(this.locations) && this.locations.length > 1) {
      cols.push('location');
    }

    return _.concat(cols, ['tapped', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', "untappdId", 'imgUrl', 'actions']);
  }

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

  requiredIfImageTransitionsEnabled(comp: ManageBeerComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null  => {
      var imageTransitionsEnabled = _.get(comp.modifyBeer.editValues, "imageTransitionsEnabled")
      
      if(!imageTransitionsEnabled){
        return null;
      }
      
      if(isNilOrEmpty(control.value)) {
        return { requiredIfImageTransitionsEnabled: true };
      }

      return null;
    }
  }

  modifyFormGroup: FormGroup = new FormGroup({
    name: new FormControl('', [this.requiredIfNoBrewTool(this)]),
    description: new FormControl('', []),
    locationId: new FormControl('', [Validators.required]),
    style: new FormControl('', [this.requiredIfNoBrewTool(this)]),
    abv: new FormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    srm: new FormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    ibu: new FormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    externalBrewingTool: new FormControl(-1),
    brewDate: new FormControl(new Date(), []),
    kegDate: new FormControl(new Date(), []),
    imgUrl: new FormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    imageTransitionsEnabled: new FormControl(''),
    emptyImgUrl: new FormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    brewfatherBatchId: new FormControl('', [this.requiredForBrewingTool(this, "brewfather")]),
    untappdId: new FormControl('')
  });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar, public dialog: MatDialog) { }

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = [];
        for(let location of locations) {
          this.locations.push(new Location(location));
        }
        this.dataService.getBeers(true).subscribe({
          next: (beers: Beer[]) => {
            this.beers = [];
            _.forEach(beers, (beer) => {
              this.beers.push(new Beer(beer))
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
    var data:any = {}
    if(this.locations.length === 1) {
      data["locationId"] = this.locations[0].id;
    }
    this.modifyBeer = new Beer(data);
    this.modifyBeer.editValues = data;
    this.adding = true;
  }

  create(): void {
    var data: any = {}
    const keys = ['name', 'description', 'locationId', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', 'imgUrl', 'externalBrewingToolMeta', 'emptyImgUrl', 'imageTransitionsEnabled']
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

    if (this.modifyBeer.imageTransitions) {
      let imageTransitions: any[] = [];
      for(let i of this.modifyBeer.imageTransitions) {
        imageTransitions.push({
          changePercent: i.editValues.changePercent,
          imgUrl: i.editValues.imgUrl
        });
      }
      if(imageTransitions){
        data["imageTransitions"] = imageTransitions;
      }
    }

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
    this.imageTransitionsToDelete = [];
    this.editing = true;
    this.modifyFormGroup.reset();
    this.reRunValidation();
  }

  save(): void {  
    this.processing = true;
    this.deleteImageTransitionRecursive();
  }

  deleteImageTransitionRecursive(): void {
    if(_.isEmpty(this.imageTransitionsToDelete)) {
      this.saveBeer();
    } else {
      let imageTransitionId = this.imageTransitionsToDelete.pop();
      if(!imageTransitionId) {
        return this.saveBeer();
      }

      this.dataService.deleteImageTransition(imageTransitionId).subscribe({
        next: (_: any) => {
          this.deleteImageTransitionRecursive()
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
    }
  }

  saveBeer(): void {
    if(isNilOrEmpty(this.changes)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editing = false;
      });
    } else {
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
      });
    }
  }

  cancelEdit(): void {
    this.modifyBeer.disableEditing();
    if(!isNilOrEmpty(this.imageTransitionsToDelete)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editing = false;
      });
    } else {
      this.editing = false;
    }
  }

  delete(beer: Beer): void {
    if(confirm(`Are you sure you want to delete beer '${beer.getName()}'?`)) {
      this.processing = true;
      if(!_.isNil(beer.taps) && beer.taps.length > 0){
        if(confirm(`The beer is associated with one or more taps.  Clear from tap(s)?`)) {
          var tapIds : string[] = [];
          _.forEach(beer.taps, (t)=>{
            tapIds.push(t.id);
          });

          this.clearFromNextTap(tapIds, () => {
              this._delete(beer);
            }, (err: DataError) => {
              this.displayError(err.message);
              this.processing = false;
            });
        }
      } else {
        this._delete(beer);
      }
    }
  }

  clearFromNextTap(tapIds: string[], next: Function, error: Function): void {
    if(isNilOrEmpty(tapIds))
      return next();

    var tapId = tapIds.pop();
    if(!tapId)
      return next();
      
    this._clearFromTap(tapId, () => { this.clearFromNextTap(tapIds, next, error) }, error);
  }

  _clearFromTap(tapId: string, next: Function, error: Function): void {
    this.dataService.clearBeerFromTap(tapId).subscribe({
      next: (resp: any) => {
        next();
      },
      error: (err: DataError) => {
        error(err);
      }
    });
  }

  _delete(beer: Beer): void {
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
    });
  }

  filter(sort?: Sort) {
    var sortBy:string = "description";
    var asc: boolean = true;

    if(!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    var filteredData: Beer[] = this.beers;

    if(!_.isEmpty(this.selectedLocationFilters)){
      filteredData = <Beer[]>_.filter(this.beers, (b) => { return this.selectedLocationFilters.includes(b.locationId) });
    }

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
    return !_.isEmpty(this.changes) || !isNilOrEmpty(this.imageTransitionsToDelete);
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
    
    if (_.has(changes, "imageTransitions") && this.modifyBeer.imageTransitions) {
      let imageTransitions : ImageTransition[] = [];
      for(let i of this.modifyBeer.imageTransitions) {
        if(i.hasChanges) {
          imageTransitions.push({id: i.id, ...i.changes});
        }
      }
      if(isNilOrEmpty(imageTransitions)) {
        delete changes["imageTransitions"];
      } else {
        changes["imageTransitions"] = imageTransitions;
      }
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

  openUploadDialog(targetObj: any, key: string): void {
    const dialogRef = this.dialog.open(FileUploadDialogComponent, {
      data: {
        imageType: "beer"
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        const f = result[0];
        _.set(targetObj, key, f.path);
      }
    });
  }

  openImageSelectorDialog(targetObj: any, key: string): void {
    const dialogRef = this.dialog.open(ImageSelectorDialogComponent, {
      width: '1200px',
      data: {
        imageType: "beer"
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        _.set(targetObj, key, result);
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

  isTapped(beer: Beer): boolean{
    return !isNilOrEmpty(beer.taps);
  }

  addImageTransition(): void {
    if(!this.modifyBeer.imageTransitions){
      this.modifyBeer.imageTransitions = [];
    }
    let i = new ImageTransition();
    i.enableEditing();
    this.modifyBeer.imageTransitions.push(i)
  }

  get areImageTransitionsValid() : boolean {
    if(_.isNil(this.modifyBeer.editValues) || _.isNil(this.modifyBeer.imageTransitions) || !this.modifyBeer.imageTransitionsEnabled) {
      return true;
    }

    for (let imageTransition of this.modifyBeer.imageTransitions) {
      if(isNilOrEmpty(imageTransition.editValues.changePercent) || isNilOrEmpty(imageTransition.editValues.imgUrl) || imageTransition.editValues.changePercent < 1 || imageTransition.editValues.changePercent > 99) {
        return false;
      }
    }
    
    return true;
  }

  removeImageTransitionItemFromList(imageTransition: ImageTransition) : void {
    if(!isNilOrEmpty(imageTransition.id)) {
      return this.removeImageTransitionItemFromListById(imageTransition);
    }

    if(isNilOrEmpty(imageTransition) || isNilOrEmpty(this.modifyBeer) || !this.modifyBeer.imageTransitions) {
      return;
    }

    let changePercent = imageTransition.isEditing ? imageTransition.editValues.changePercent : imageTransition.editValues;
    let imgUrl = imageTransition.isEditing ? imageTransition.editValues.imgUrl : imageTransition.imgUrl;
    let list: ImageTransition[] = [];
    for(let i of this.modifyBeer.imageTransitions) {
      let _changePercent = i.isEditing ? i.editValues.changePercent : i.editValues;
      let _imgUrl = i.isEditing ? i.editValues.imgUrl : i.imgUrl;
      if(_changePercent !== changePercent && _imgUrl !== imgUrl) {
        list.push(i)
      }
    }
    this.modifyBeer.imageTransitions = list;
  }

  removeImageTransitionItemFromListById(imageTransition: ImageTransition) : void {
    if(isNilOrEmpty(imageTransition) || isNilOrEmpty(imageTransition.id) || isNilOrEmpty(this.modifyBeer) || !this.modifyBeer.imageTransitions) {
      return;
    }

    let list: ImageTransition[] = [];
    for(let i of this.modifyBeer.imageTransitions) {
      if(i.id !== imageTransition.id) {
        list.push(i)
      }
    }
    this.modifyBeer.imageTransitions = list;
    this.imageTransitionsToDelete.push(imageTransition.id);
  }

  getDescriptionDisplay(beer: Beer) : string {
    let desc = beer.getDescription();

    if(isNilOrEmpty(desc)) {
      return "";
    }
    if(this.isDescriptionTooLong(beer)) {
      return _.truncate(desc, {'length': 48});
    }
    return desc;
  }

  isDescriptionTooLong(beer: Beer) : boolean {
    let desc = beer.getDescription();

    if(isNilOrEmpty(desc)) {
      return false;
    }
    if(_.size(desc) > 48) {
      return true;
    }
    return false;
  }
}
