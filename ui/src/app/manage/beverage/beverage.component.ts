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

import { Beverage, ImageTransition, Settings, Location, UserInfo } from '../../models/models';
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
  locations: Location[] = [];
  selectedLocationFilters: string[] = [];
  _ = _;
  imageTransitionsToDelete: string[] = [];

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

  modifyFormGroup: UntypedFormGroup = new UntypedFormGroup({
    name: new UntypedFormControl('', [Validators.required]),
    type: new UntypedFormControl('', [Validators.required]),
    description: new UntypedFormControl('', []),
    locationId: new UntypedFormControl('', [Validators.required]),
    brewery: new UntypedFormControl('', []),
    breweryLink: new UntypedFormControl('', []),
    flavor: new UntypedFormControl('', []),
    imgUrl: new UntypedFormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    imageTransitionsEnabled: new UntypedFormControl(''),
    emptyImgUrl: new UntypedFormControl('', [this.requiredIfImageTransitionsEnabled(this)]),
    roastery: new UntypedFormControl('', []),
    roasteryLink: new UntypedFormControl('', []),
  });

  get displayedColumns() {
    var cols = ['name', 'description'];

    if(!isNilOrEmpty(this.locations) && this.locations.length > 1) {
      cols.push('location');
    }

    return _.concat(cols, ['tapped', "type", "brewery", "roastery", "flavor", "imgUrl", "actions"]);
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

  add(): void {
    this.modifyFormGroup.reset();
    var data: any = {type: this.defaultType, meta: {}}
    if(this.locations.length === 1) {
      data["locationId"] = this.locations[0].id;
    }
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
      locationId: this.modifyBeverage.editValues.locationId,
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
      this.saveBeverage();
    } else {
      let imageTransitionId = this.imageTransitionsToDelete.pop();
      if(!imageTransitionId) {
        return this.saveBeverage();
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

  saveBeverage(): void {
    if(isNilOrEmpty(this.changes)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editing = false;
      });
    } else {
      this.dataService.updateBeverage(this.modifyBeverage.id, this.changes).subscribe({
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
  }

  cancelEdit(): void {
    this.modifyBeverage.disableEditing();
    if(!isNilOrEmpty(this.imageTransitionsToDelete)) {
      this.refresh(()=> {this.processing = false;}, () => {
        this.editing = false;
      });
    } else {
      this.editing = false;
    }
  }

  delete(beverage: Beverage): void {
    if(confirm(`Are you sure you want to delete beverage '${beverage.name}'?`)) {
      this.processing = true;
      if(!_.isNil(beverage.taps) && beverage.taps.length > 0){
        if(confirm(`The beverage is associated with one or more taps.  Clear from tap(s)?`)) {
          var tapIds : string[] = [];
          _.forEach(beverage.taps, (t)=>{
            tapIds.push(t.id);
          });

          this.clearFromNextTap(tapIds, () => {
              this._delete(beverage);
            }, (err: DataError) => {
              this.displayError(err.message);
              this.processing = false;
            });
        }
      } else {
        this._delete(beverage);
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
    this.dataService.clearBeverageFromTap(tapId).subscribe({
      next: (resp: any) => {
        next();
      },
      error: (err: DataError) => {
        error(err);
      }
    });
  }

  _delete(beverage: Beverage) {
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

  get hasChanges(): boolean {
    return !_.isEmpty(this.changes) || !isNilOrEmpty(this.imageTransitionsToDelete);
  }

  get changes(): any {
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

    if(!_.isEmpty(this.selectedLocationFilters)){
      filteredData = <Beverage[]>_.filter(this.beverages, (b) => { return this.selectedLocationFilters.includes(b.locationId) });
    }

    
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

  reRunValidation(): void {
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

  isTapped(beverage: Beverage): boolean{
    return !isNilOrEmpty(beverage.taps);
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
}
