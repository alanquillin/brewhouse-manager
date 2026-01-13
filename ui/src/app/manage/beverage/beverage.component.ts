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

import { Beverage, ImageTransition, Settings, Location, UserInfo, Batch, Tap } from '../../models/models';
import { isNilOrEmpty } from '../../utils/helpers';
import { toUnixTimestamp, convertUnixTimestamp } from '../../utils/datetime';

import * as _ from 'lodash';

@Component({
    selector: 'app-beverages',
    templateUrl: './beverage.component.html',
    styleUrls: ['./beverage.component.scss'],
    standalone: false
})
export class ManageBeverageComponent implements OnInit {

  loading = false;
  beverages: Beverage[] = [];
  filteredBeverages: Beverage[] = [];
  processing = false;
  addingBeverage = false;
  editingBeverage = false;
  addingBatch = false;
  editingBatch = false;
  showArchivedBatches: boolean = false;
  modifyBeverage: Beverage = new Beverage();
  selectedBatchBeverage: Beverage = new Beverage();
  modifyBatch: Batch = new Batch();
  isNilOrEmpty: Function = isNilOrEmpty;
  defaultType!: string;
  supportedTypes: string[] = [];
  locations: Location[] = [];
  selectedLocationFilters: string[] = [];
  _ = _;
  imageTransitionsToDelete: string[] = [];
  beverageBatches: {[batchId: string]: Batch[]} = {};

  userInfo!: UserInfo;

  requiredIfImageTransitionsEnabled(comp: ManageBeverageComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null  => {
      var imageTransitionsEnabled = _.get(comp.modifyBeverage.editValues, "imageTransitionsEnabled")
      
      if(!imageTransitionsEnabled){
        return null;
      }
      
      if(isNilOrEmpty(control.value)) {
        return { requiredIfImageTransitionsEnabled: true };
      }

      return null;
    }
  }

  modifyBeverageFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [Validators.required]),
    type: new UntypedFormControl('', [Validators.required]),
    description: new UntypedFormControl('', []),
    brewery: new UntypedFormControl('', []),
    breweryLink: new UntypedFormControl('', []),
    flavor: new UntypedFormControl('', []),
    imgUrl: new UntypedFormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    imageTransitionsEnabled: new UntypedFormControl(''),
    emptyImgUrl: new UntypedFormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    roastery: new UntypedFormControl('', []),
    roasteryLink: new UntypedFormControl('', []),
  });

  modifyBatchFormGroup: UntypedFormGroup = new UntypedFormGroup({
    batchNumber: new UntypedFormControl('', [Validators.required]),
    locationIds: new UntypedFormControl('', [Validators.required]),
    brewDate: new UntypedFormControl(new Date(), [Validators.required]),
    kegDate: new UntypedFormControl(new Date(), [Validators.required]),
  });

  get displayedColumns(): string[] {
    return ['name', 'description', 'batchCount', 'tapped', "type", "brewery", "roastery", "flavor", "imgUrl", "actions"];
  }

  get displayedBatchColumns(): string[] {
    var cols = ["batchNumber", "tapped"];

    if(!isNilOrEmpty(this.locations) && this.locations.length > 1) {
      cols.push('locations');
    }

    return _.concat(cols, ["brewDate", "kegDate", 'actions']);
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
        
        this.dataService.getLocations().subscribe({
          next: (locations: Location[]) => {
            this.locations = [];
            for(let location of _.sortBy(locations, [(l:Location) => {return l.description}])) {
              this.locations.push(new Location(location));
            }
            this.dataService.getBeverages(true).subscribe({
              next: (beverages: Beverage[]) => {
                this.beverages = [];
                _.forEach(beverages, (beverage) => {
                  var _beverage = new Beverage(beverage)
                  this.beverages.push(_beverage)
                  this.beverageBatches[beverage.id] = [];
                  this.dataService.getBeverageBatches(beverage.id, true, this.showArchivedBatches).subscribe({
                    next: (batches: Batch[]) =>{
                      _.forEach(batches, (_batch) => {
                        var batch = new Batch(_batch)
                        this.beverageBatches[beverage.id].push(batch);
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

  addBeverage(): void {
    this.modifyBeverageFormGroup.reset();
    var data: any = {type: this.defaultType, meta: {}}
    if(this.locations.length === 1) {
      data["locationId"] = this.locations[0].id;
    }
    this.modifyBeverage = new Beverage(data);
    this.modifyBeverage.editValues = data;
    this.addingBeverage = true;
  }

  dateToNumber(v: any) : number | undefined {
    return isNilOrEmpty(v) ? undefined : _.isDate(v) ? toUnixTimestamp(v) : _.toNumber(v);
  }

  createBeverage(): void {
    this.processing = true;
    var data: any = {
      name: this.modifyBeverage.editValues.name,
      description: this.modifyBeverage.editValues.description,
      type: this.modifyBeverage.editValues.type,
      brewery: this.modifyBeverage.editValues.brewery,
      breweryLink: this.modifyBeverage.editValues.breweryLink,
      flavor: this.modifyBeverage.editValues.flavor,
      imgUrl: this.modifyBeverage.editValues.imgUrl,
      meta: this.modifyBeverage.editValues.meta,
      emptyImgUrl: this.modifyBeverage.editValues.emptyImgUrl,
      imageTransitionsEnabled: this.modifyBeverage.editValues.imageTransitionsEnabled
    }

    if (this.modifyBeverage.imageTransitions) {
      let imageTransitions: ImageTransition[] = [];
      for(let i of this.modifyBeverage.imageTransitions) {
        imageTransitions.push(i);
      }
      if(imageTransitions){
        data["imageTransitions"] = imageTransitions;
      }
    }
    
    this.dataService.createBeverage(data).subscribe({
      next: (beverage: Beverage) => {
        this.refresh(() => {this.processing = false;}, () => {this.addingBeverage = false;});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  cancelAddBeverage(): void {
    this.addingBeverage = false;
  }

  editBeverage(beverage: Beverage): void {
    beverage.enableEditing();
    this.modifyBeverage = beverage;
    this.imageTransitionsToDelete = [];
    this.editingBeverage = true;
    this.modifyBeverageFormGroup.reset();
    this.reRunBeverageValidation();
  }

  saveBeverage(): void {
    this.processing = true;
    this.deleteImageTransitionRecursive();
  }

  deleteImageTransitionRecursive(): void {
    if(_.isEmpty(this.imageTransitionsToDelete)) {
      this.saveBeverageActual();
    } else {
      let imageTransitionId = this.imageTransitionsToDelete.pop();
      if(!imageTransitionId) {
        return this.saveBeverageActual();
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

  saveBeverageActual(): void {
    if(isNilOrEmpty(this.beverageChanges)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editingBeverage = false;
      });
    } else {
      this.dataService.updateBeverage(this.modifyBeverage.id, this.beverageChanges).subscribe({
        next: (beverage: Beverage) => {
          this.modifyBeverage.disableEditing();
          this.refresh(()=> {this.processing = false;}, () => {
            this.editingBeverage = false;
          })
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      })
    }
  }

  cancelEditBeverage(): void {
    this.modifyBeverage.disableEditing();
    if(!isNilOrEmpty(this.imageTransitionsToDelete)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editingBeverage = false;
      });
    } else {
      this.editingBeverage = false;
    }
  }

  deleteBeverage(beverage: Beverage): void {
    if(confirm(`Are you sure you want to delete beverage '${beverage.name}'?`)) {
      this.processing = true;
      var tapIds = this.beverageBatchesAssocTaps(beverage);
      if(!isNilOrEmpty(tapIds)){
        if(confirm(`The beverage has 1 or more batch(es) associated with one or more taps.  Batches must first be cleared from the tap(s) before deleting. Proceed?`)) {
          this.clearNextTap(tapIds, () => {
              this._deleteBeverage(beverage);
            }, (err: DataError) => {
              this.displayError(err.message);
              this.processing = false;
            });
        }
      } else {
        this._deleteBeverage(beverage);
      }
    }
  }

  beverageBatchesAssocTaps(beverage: Beverage): string[] {
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

  _deleteBeverage(beverage: Beverage) {
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

  get hasBeverageChanges(): boolean {
    return !_.isEmpty(this.beverageChanges) || !isNilOrEmpty(this.imageTransitionsToDelete);
  }

  get beverageChanges(): any {
    var changes = _.cloneDeep(this.modifyBeverage.changes);
    
    if (_.has(changes, "imageTransitions") && this.modifyBeverage.imageTransitions) {
      let imageTransitions : ImageTransition[] = [];
      for(let i of this.modifyBeverage.imageTransitions) {
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

    return changes;
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
    return this.modifyBeverageFormGroup.controls;
  }

  reRunBeverageValidation(): void {
    _.forEach(this.modifyForm, (ctrl) => {
      ctrl.updateValueAndValidity();
    });
  }

  openUploadDialog(targetObj: any, key: string): void {
    const dialogRef = this.dialog.open(FileUploadDialogComponent, {
      data: {
        imageType: "beverage"
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
        imageType: "beverage"
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

  isBeverageTapped(beer: Beverage): boolean {
    var isTapped = false;
    _.forEach(this.beverageBatches[beer.id], (batch) => {
      if(!isNilOrEmpty(batch.taps)) {
        isTapped = true;
      }
    })
    return isTapped;
  }

  beverageAssocTaps(beer: Beverage): Tap[] {
    var tapIds: Tap[] = [];

    _.forEach(this.beverageBatches[beer.id], (batch) => {
      if(!isNilOrEmpty(batch.taps)) {
        _.forEach(batch.taps, (tap) => {
          tapIds.push(tap);
        })
      }
    })
    return tapIds
  }

  addImageTransition(): void {
    if(!this.modifyBeverage.imageTransitions){
      this.modifyBeverage.imageTransitions = [];
    }
    let i = new ImageTransition();
    i.enableEditing();
    this.modifyBeverage.imageTransitions.push(i)
  }

  get areImageTransitionsValid() : boolean {
    if(_.isNil(this.modifyBeverage.editValues) || _.isNil(this.modifyBeverage.imageTransitions) || !this.modifyBeverage.imageTransitionsEnabled) {
      return true;
    }

    for (let imageTransition of this.modifyBeverage.imageTransitions) {
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

    if(isNilOrEmpty(imageTransition) || isNilOrEmpty(this.modifyBeverage) || !this.modifyBeverage.imageTransitions) {
      return;
    }

    let changePercent = imageTransition.isEditing ? imageTransition.editValues.changePercent : imageTransition.editValues;
    let imgUrl = imageTransition.isEditing ? imageTransition.editValues.imgUrl : imageTransition.imgUrl;
    let list: ImageTransition[] = [];
    for(let i of this.modifyBeverage.imageTransitions) {
      let _changePercent = i.isEditing ? i.editValues.changePercent : i.editValues;
      let _imgUrl = i.isEditing ? i.editValues.imgUrl : i.imgUrl;
      if(_changePercent !== changePercent && _imgUrl !== imgUrl) {
        list.push(i)
      }
    }
    this.modifyBeverage.imageTransitions = list;
  }

  removeImageTransitionItemFromListById(imageTransition: ImageTransition) : void {
    if(isNilOrEmpty(imageTransition) || isNilOrEmpty(imageTransition.id) || isNilOrEmpty(this.modifyBeverage) || !this.modifyBeverage.imageTransitions) {
      return;
    }

    let list: ImageTransition[] = [];
    for(let i of this.modifyBeverage.imageTransitions) {
      if(i.id !== imageTransition.id) {
        list.push(i)
      }
    }
    this.modifyBeverage.imageTransitions = list;
    this.imageTransitionsToDelete.push(imageTransition.id);
  }

  getDescriptionDisplay(beverage: Beverage) : string {
    if(isNilOrEmpty(beverage.description)) {
      return "";
    }

    if(this.isDescriptionTooLong(beverage)) {
      return _.truncate(beverage.description, {'length': 48});
    }
    return beverage.description;
  }

  isDescriptionTooLong(beverage: Beverage) : boolean {
    if(isNilOrEmpty(beverage)) {
      return false;
    }

    if(_.size(beverage.description) > 48) {
      return true;
    }
    return false;
  }

  isBatchTapped(batch: Batch): boolean {
    return !isNilOrEmpty(batch.taps);
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

    const keys = ['batchNumber', 'kegDate', 'brewDate']
    _.forEach(keys, (k) => {
      if(_.has(changes, k)) {
        if(isNilOrEmpty(changes[k])) {
          changes[k] = null;
        }
      }
    });
    return changes;
  }
  
  addBatch(beer: Beverage): void {
    this.selectedBatchBeverage = beer;
    this.modifyBeverageFormGroup.reset();
    var data:any = {};
    this.modifyBatch = new Batch(data);
    this.modifyBatch.editValues = data;
    this.addingBatch = true;
  }

  createBatch(): void {
    this.processing = true;
    
    var data: any = {
      beverageId: this.selectedBatchBeverage.id,
      batchNumber: this.modifyBatch.editValues.batchNumber,
      locationIds: this.modifyBatch.editValues.locationIds,
      brewDate: this.dateToNumber(this.modifyBatch.editValues.brewDateObj),
      kegDate: this.dateToNumber(this.modifyBatch.editValues.kegDateObj)
    }
    
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

  editBatch(batch: Batch, beverage: Beverage): void {
    this.selectedBatchBeverage = beverage;
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
    if(confirm(`Are you sure you want to archive the batch keg'd on ${batch.getKegDate() }?`)) {
      this.processing = true;
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
  }

  _archiveBatch(batch: Batch): void {
    this.processing = true;
    this.dataService.updateBatch(batch.id, {archivedOn: convertUnixTimestamp(Date.now())}).subscribe({
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

  toggleArchivedBatches(): void {
    this.showArchivedBatches = !this.showArchivedBatches;
    if (this.editingBeverage && this.modifyBeverage && this.modifyBeverage.id) {
      this.dataService.getBeverageBatches(this.modifyBeverage.id, true, this.showArchivedBatches).subscribe({
        next: (batches: Batch[]) => {
          this.beverageBatches[this.modifyBeverage.id] = [];
          _.forEach(batches, (_batch) => {
            this.beverageBatches[this.modifyBeverage.id].push(new Batch(_batch));
          });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
        }
      });
    }
  }

  isArchivedBatch(batch: Batch): boolean {
    return !isNilOrEmpty(batch.archivedOn);
  }
}
