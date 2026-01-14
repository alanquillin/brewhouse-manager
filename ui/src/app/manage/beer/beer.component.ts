import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { UntypedFormControl, AbstractControl, ValidatorFn, ValidationErrors, Validators, UntypedFormGroup } from '@angular/forms';

import { FileUploadDialogComponent } from '../../_dialogs/file-upload-dialog/file-upload-dialog.component';
import { ImageSelectorDialogComponent } from '../../_dialogs/image-selector-dialog/image-selector-dialog.component'
import { LocationImageDialog } from '../../_dialogs/image-preview-dialog/image-preview-dialog.component'

import { Beer, beerTransformFns, ImageTransition, Location, UserInfo, Batch, Tap } from '../../models/models';
import { isNilOrEmpty } from '../../utils/helpers';
import { convertUnixTimestamp, toUnixTimestamp } from '../../utils/datetime';


import * as _ from 'lodash';

@Component({
    selector: 'app-beer',
    templateUrl: './beer.component.html',
    styleUrls: ['./beer.component.scss'],
    standalone: false
})
export class ManageBeerComponent implements OnInit {
  loading = false;
  loadingBatches = false;
  beers: Beer[] = [];
  filteredBeers: Beer[] = [];
  beerBatches: {[batchId: string]: Batch[]} = {};
  processing = false;
  adding = false;
  editing = false;
  addingBatch = false;
  editingBatch = false;
  showArchivedBatches: boolean = false;
  modifyBeer: Beer = new Beer();
  selectedBatchBeer: Beer = new Beer();
  modifyBatch: Batch = new Batch();
  isNilOrEmpty: Function = isNilOrEmpty;
  imageTransitionsToDelete: string[] = [];
  locations: Location[] = [];
  selectedLocationFilters: string[] = [];
  _ = _;

  transformFns = beerTransformFns;

  externalBrewingTools: string[] = ["brewfather"]

  userInfo!: UserInfo;

  get displayedColumns() {
    return ['name', 'description', 'batchCount', 'tapped', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', "untappdId", 'imgUrl', 'actions'];
  }

  get displayedBatchColumns() { 
    var cols: string[] = ["batchNumber", "name", "tapped", ]

    if(!isNilOrEmpty(this.locations) && this.locations.length > 1) {
      cols.push('locations');
    }

    return _.concat(cols, ['externalBrewingTool', 'abv', 'ibu', 'srm', "brewDate", "kegDate", 'imgUrl', 'actions']);
  }

  decimalRegex = /^-?\d*[.]?\d{0,2}$/;
  decimalValidator = Validators.pattern(this.decimalRegex); 

  requiredIfNoBrewTool(comp: ManageBeerComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null  => {
      var brewTool = _.get(comp.modifyBatch.editValues, "externalBrewingTool")
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
      var brewTool = _.get(comp.modifyBatch.editValues, "externalBrewingTool")
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

  modifyBeerFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [this.requiredIfNoBrewTool(this)]),
    description: new UntypedFormControl('', []),
    style: new UntypedFormControl('', [this.requiredIfNoBrewTool(this)]),
    abv: new UntypedFormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    srm: new UntypedFormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    ibu: new UntypedFormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    externalBrewingTool: new UntypedFormControl(-1),
    imgUrl: new UntypedFormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    imageTransitionsEnabled: new UntypedFormControl(''),
    emptyImgUrl: new UntypedFormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    brewfatherRecipeId: new UntypedFormControl('', [this.requiredForBrewingTool(this, "brewfather")]),
    untappdId: new UntypedFormControl('')
  });

  modifyBatchFormGroup: UntypedFormGroup = new UntypedFormGroup({
    batchNumber: new UntypedFormControl('', [this.decimalValidator, this.requiredIfNoBrewTool(this)]),
    locationIds: new UntypedFormControl('', [Validators.required]),
    abv: new UntypedFormControl('', [this.decimalValidator]),
    srm: new UntypedFormControl('', [this.decimalValidator]),
    ibu: new UntypedFormControl('', [this.decimalValidator]),
    name: new UntypedFormControl('', []),
    externalBrewingTool: new UntypedFormControl(-1),
    brewfatherBatchId: new UntypedFormControl('', [this.requiredForBrewingTool(this, "brewfather")]),
    brewDate: new UntypedFormControl(new Date(), [this.requiredIfNoBrewTool(this)]),
    kegDate: new UntypedFormControl(new Date(), [this.requiredIfNoBrewTool(this)]),
    imgUrl: new UntypedFormControl('', []),
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
        for(let location of _.sortBy(locations, [(l:Location) => {return l.description}])) {
          this.locations.push(new Location(location));
        }
        this.dataService.getBeers().subscribe({
          next: (beers: Beer[]) => {
            this.beers = [];
            _.forEach(beers, (_beer) => {
              var beer = new Beer(_beer);
              this.beers.push(beer)
              this.beerBatches[beer.id] = [];
              this.dataService.getBeerBatches(beer.id, true, this.showArchivedBatches).subscribe({
                next: (batches: Batch[]) =>{
                  _.forEach(batches, (_batch) => {
                    var batch = new Batch(_batch)
                    this.beerBatches[beer.id].push(batch);
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
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = userInfo;

        if(this.userInfo.locations && this.userInfo.admin) {
          for(let l of this.userInfo.locations) {
            this.selectedLocationFilters.push(l.id);
          }
        }
        this.refresh(()=> {
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

  addBeer(): void {
    this.modifyBeerFormGroup.reset();
    var data:any = {}
    if(this.locations.length === 1) {
      data["locationId"] = this.locations[0].id;
    }
    this.modifyBeer = new Beer(data);
    this.modifyBeer.editValues = data;
    this.adding = true;
  }

  createBeer(): void {
    var data: any = {}
    const keys = ['name', 'description', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'imgUrl', 'externalBrewingToolMeta', 'emptyImgUrl', 'imageTransitionsEnabled']
    const checkKeys = {}
    
    _.forEach(keys, (k) => {
      const checkKey: any = _.get(checkKeys, k, k);

      var val: any = _.get(this.modifyBeer.editValues, checkKey);
      if(isNilOrEmpty(val)){
        return;
      }
      const transformFn: any = _.get(this.transformFns, k);
      if(!_.isNil(transformFn) && typeof transformFn === 'function'){
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
        var _beer = new Beer(beer);
        this.beers.push(_beer);
        this.beerBatches[_beer.id] = [];
        this.filter();
        this.adding = false;
        this.editBeer(_beer, false);
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  cancelAddBeer(): void {
    this.adding = false;
  }

  editBeer(beer: Beer, refresh: boolean = true): void {
    beer.enableEditing();
    this.modifyBeer = beer;
    this.imageTransitionsToDelete = [];
    this.editing = true;
    if (refresh) {
      this.modifyBeerFormGroup.reset();
      this.reRunBeerValidation();
    }
  }

  saveBeer(): void {  
    this.processing = true;
    this.deleteImageTransitionRecursive();
  }

  deleteImageTransitionRecursive(): void {
    if(_.isEmpty(this.imageTransitionsToDelete)) {
      this.saveBeerActual();
    } else {
      let imageTransitionId = this.imageTransitionsToDelete.pop();
      if(!imageTransitionId) {
        return this.saveBeerActual();
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

  saveBeerActual(): void {
    if(isNilOrEmpty(this.beerChanges)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editing = false;
      });
    } else {
      this.dataService.updateBeer(this.modifyBeer.id, this.beerChanges).subscribe({
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

  cancelEditBeer(): void {
    this.modifyBeer.disableEditing();
    if(!isNilOrEmpty(this.imageTransitionsToDelete)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editing = false;
      });
    } else {
      this.editing = false;
    }
  }

  deleteBeer(beer: Beer): void {
    if(confirm(`Are you sure you want to delete beer '${beer.getName()}'?`)) {
      this.processing = true;
      var tapIds = this.beerBatchesAssocTaps(beer);
      if(!isNilOrEmpty(tapIds)){
        if(confirm(`The beer has 1 or more batch associated with one or more taps.  Batches must first be cleared from the tap(s) before deleting. Proceed?`)) {
          this.clearNextTap(tapIds, () => {
              this._deleteBeer(beer);
            }, (err: DataError) => {
              this.displayError(err.message);
              this.processing = false;
            });
        }
      } else {
        this._deleteBeer(beer);
      }
    }
  }

  beerBatchesAssocTaps(beer: Beer): string[] {
    var tapIds : string[] = [];

    return tapIds
  }

  clearNextTap(tapIds: string[], next: Function, error: Function): void {
    if(isNilOrEmpty(tapIds))
      return next();

    var tapId = tapIds.pop();
    if(!tapId)
      return next();
      
    this.clearTap(tapId, () => { this.clearNextTap(tapIds, next, error) }, error);
  }

  clearTap(tapId: string, next: Function, error: Function): void {
    this.dataService.clearTap(tapId).subscribe({
      next: (resp: any) => {
        next();
      },
      error: (err: DataError) => {
        error(err);
      }
    });
  }

  _deleteBeer(beer: Beer): void {
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

  beerBrewToolChanges(event?: any) {
    this.addMissingBeerMeta();
    this.reRunBeerValidation();
  }

  addMissingBeerMeta() {
    switch(this.modifyBeer.editValues.externalBrewingTool) {
      case "brewfather":
        if(!_.has(this.modifyBeer.editValues.externalBrewingToolMeta, "recipeId")){
          _.set(this.modifyBeer.editValues, 'externalBrewingToolMeta.recipeId', '');
        }
        break
    }
  }

  get modifyBeerForm(): { [key: string]: AbstractControl } {
    return this.modifyBeerFormGroup.controls;
  } 

  reRunBeerValidation(): void {
    _.forEach(this.modifyBeerForm, (ctrl) => {
      ctrl.updateValueAndValidity();
    });
  }

  get hasBeerChanges(): boolean {
    return !_.isEmpty(this.beerChanges) || !isNilOrEmpty(this.imageTransitionsToDelete);
  }

  get beerChanges(): any {
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

    const keys = ['name', 'description', 'style', 'abv', 'ibu', 'srm', 'imgUrl']
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

    var recipeId = _.get(beer.externalBrewingToolMeta, "recipeId");
    if (beer.externalBrewingTool === "brewfather" && beer.externalBrewingToolMeta && !isNilOrEmpty(recipeId)) {
      return `https://web.brewfather.app/tabs/recipes/recipe/${recipeId}`;
    }

    return "";
  }

  getBatchLink(batch: Batch) : string {
    if (_.isNil(batch))
      return "";

    var batchId = _.get(batch.externalBrewingToolMeta, "batchId");
    if (batch.externalBrewingTool === "brewfather" && batch.externalBrewingToolMeta && !isNilOrEmpty(batchId)) {
      return `https://web.brewfather.app/tabs/batches/batch/${batchId}`;
    }

    return "";
  }

  isBeerTapped(beer: Beer): boolean {
    var isTapped = false;
    _.forEach(this.beerBatches[beer.id], (batch) => {
      if(!isNilOrEmpty(batch.taps)) {
        isTapped = true;
      }
    })
    return isTapped;
  }

  beerAssocTaps(beer: Beer): Tap[] {
    var tapIds: Tap[] = [];

    _.forEach(this.beerBatches[beer.id], (batch) => {
      if(!isNilOrEmpty(batch.taps)) {
        _.forEach(batch.taps, (tap) => {
          tapIds.push(tap);
        })
      }
    })
    return tapIds
  }

  isBatchTapped(batch: Batch): boolean {
    return !isNilOrEmpty(batch.taps);
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

  batchBrewToolChanges(event?: any) {
    this.addMissingBatchMeta();
    this.reRunBatchValidation();
  }

  addMissingBatchMeta() {
    switch(this.modifyBatch.editValues.externalBrewingTool) {
      case "brewfather":
        if(!_.has(this.modifyBatch.editValues.externalBrewingToolMeta, "batchId")){
          _.set(this.modifyBatch.editValues, 'externalBrewingToolMeta.batchId', '');
        }
        break
    }
  }

  get modifyBatchForm(): { [key: string]: AbstractControl } {
    return this.modifyBatchFormGroup.controls;
  } 

  reRunBatchValidation(): void {
    _.forEach(this.modifyBatchForm, (ctrl) => {
      ctrl.updateValueAndValidity();
    });
  }

  get hasBatchChanges(): boolean {
    return !_.isEmpty(this.batchChanges);
  }

  get batchChanges(): any {
    var changes = _.cloneDeep(this.modifyBatch.changes);

    if (_.get(changes, "externalBrewingTool") === "-1") {
      changes["externalBrewingTool"] = null;
      changes["externalBrewingToolMeta"] = null;
    } else {
      if (_.has(changes, "externalBrewingToolMeta")) {
        if(isNilOrEmpty(_.get(this.modifyBatch, "externalBrewingTool"))) {
          delete changes["externalBrewingToolMeta"];
        }
      }
    }

    const keys = ['batchNumber', 'abv', 'ibu', 'srm', 'kegDate', 'brewDate']
    _.forEach(keys, (k) => {
      if(_.has(changes, k)) {
        if(isNilOrEmpty(changes[k])) {
          changes[k] = null;
        }
      }
    });
    return changes;
  }
  
  addBatch(beer: Beer): void {
    this.selectedBatchBeer = beer;
    this.modifyBatchFormGroup.reset();
    var data:any = {};
    this.modifyBatch = new Batch(data);
    this.modifyBatch.editValues = data;
    this.addingBatch = true;
  }

  createBatch(): void {
    var data: any = {beerId: this.selectedBatchBeer.id}
    const keys = ['externalBrewingTool', 'abv', 'ibu', 'srm', 'externalBrewingToolMeta', 'batchNumber', 'name', 'imgUrl', 'locationIds']
    const dateKeys = ['brewDateObj', 'kegDateObj'];
    const checkKeys = {}
    
    _.forEach(keys, (k) => {
      const checkKey: any = _.get(checkKeys, k, k);

      var val: any = _.get(this.modifyBatch.editValues, checkKey);
      if(isNilOrEmpty(val)){
        return;
      }
      const transformFn: any = _.get(this.transformFns, k);
      if(!_.isNil(transformFn) && typeof transformFn === 'function'){
        val = transformFn(val);
      }
      data[k] = val;
    });

    _.forEach(dateKeys, (k) => {
      let _k = k.replace("Obj", "");

      var val: any = _.get(this.modifyBatch.editValues, k);
      if(isNilOrEmpty(val)){
        return;
      }

      val = toUnixTimestamp(val);
      const transformFn: any = _.get(this.transformFns, _k);
      if(!_.isNil(transformFn) && typeof transformFn === 'function'){
        val = transformFn(val);
      }
      data[_k] = val
    });

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
    this.dataService.createBatch(data).subscribe({
      next: (batch: Batch) => {
        this.refresh(() => {this.processing = false;}, () => {this.addingBatch = false;});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  cancelAddBatch(): void {
    this.addingBatch = false;
  }

  editBatch(batch: Batch, beer: Beer): void {
    this.selectedBatchBeer = beer;
    batch.enableEditing();
    this.modifyBatch = batch;
    this.editingBatch = true;
    this.modifyBatchFormGroup.reset();
    this.reRunBatchValidation();
  }

  saveBatch(): void {  
    this.processing = true;
    if(isNilOrEmpty(this.batchChanges)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editingBatch = false;
      });
    } else {
      this.dataService.updateBatch(this.modifyBatch.id, this.batchChanges).subscribe({
        next: (batch: Batch) => {
          this.refresh(()=> {this.processing = false;}, () => {
            this.editingBatch = false;
          })
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      });
    }
  }

  cancelEditBatch(): void {
    this.modifyBatch.disableEditing();
    this.editingBatch = false;
  }

  archiveBatch(batch: Batch): void {
    this.processing = true;
    this.dataService.getBatch(batch.id, true).subscribe({
      next: (_batch: Batch) => {
        batch = new Batch(_batch);
        if(confirm(`Are you sure you want to archive the batch keg'd on ${batch.getKegDate() }?`)) {  
          if(!_.isNil(batch.taps) && batch.taps.length > 0){
            var tapIds : string[] = []
            _.forEach(batch.taps, (tap) => {
              tapIds.push(tap.id)
            });
            if(confirm(`The batch is associated with one or more taps.  It will need to be cleared from tap(s) before archiving.  Proceed?`)) {
              this.clearNextTap(tapIds, () => {
                  this._archiveBatch(batch);
                }, (err: DataError) => {
                  this.displayError(err.message);
                  this.processing = false;
                });
            }
          } else {
            this._archiveBatch(batch);
          }
        }
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  _archiveBatch(batch: Batch): void {
    this.processing = true;
    this.loadingBatches = true;
    this.dataService.updateBatch(batch.id, {archivedOn: convertUnixTimestamp(Date.now())}).subscribe({
      next: (resp: any) => {
        this.processing = false;
        this.loading = true;
        this.refresh(()=>{this.loading = false; this.loadingBatches = false;});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
        this.loadingBatches = false;
      }
    });
  }

  unarchiveBatch(batch: Batch): void {
    if(confirm(`Are you sure you want to unarchive the batch keg'd on ${batch.getKegDate() }?`)) {
      this.processing = true;
      this.loadingBatches = true;
      this.dataService.updateBatch(batch.id, {archivedOn: null}).subscribe({
        next: (resp: any) => {
          this.processing = false;
          this.loading = true;
          this.refresh(()=>{this.loading = false; this.loadingBatches = false;});
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
          this.loadingBatches = false;
        }
      });
    }
  }

  toggleArchivedBatches(): void {
    this.loadingBatches = true
    if (this.editing && this.modifyBeer && this.modifyBeer.id) {
      this.dataService.getBeerBatches(this.modifyBeer.id, true, this.showArchivedBatches).subscribe({
        next: (batches: Batch[]) => {
          this.beerBatches[this.modifyBeer.id] = [];
          _.forEach(batches, (_batch) => {
            this.beerBatches[this.modifyBeer.id].push(new Batch(_batch));
          });
          this.loadingBatches = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.loadingBatches = false;
        }
      });
    }
  }

  isArchivedBatch(batch: Batch): boolean {
    return !isNilOrEmpty(batch.archivedOn);
  }
}
