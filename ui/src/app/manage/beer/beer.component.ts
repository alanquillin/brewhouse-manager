import { Component, OnInit, ViewChild } from '@angular/core';
import {
  AbstractControl,
  UntypedFormControl,
  UntypedFormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort } from '@angular/material/sort';
import { Router } from '@angular/router';
import { CurrentUserService } from '../../_services/current-user.service';
import { DataError, DataService } from '../../_services/data.service';

import { FileUploadDialogComponent } from '../../_dialogs/file-upload-dialog/file-upload-dialog.component';
import { LocationImageDialogComponent } from '../../_dialogs/image-preview-dialog/image-preview-dialog.component';
import { ImageSelectorDialogComponent } from '../../_dialogs/image-selector-dialog/image-selector-dialog.component';

import {
  Batch,
  Beer,
  beerTransformFns,
  ImageTransition,
  Location,
  Tap,
  UserInfo,
} from '../../models/models';
import { convertUnixTimestamp, toUnixTimestamp } from '../../utils/datetime';
import { isNilOrEmpty } from '../../utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-beer',
  templateUrl: './beer.component.html',
  styleUrls: ['./beer.component.scss'],
  standalone: false,
})
export class ManageBeerComponent implements OnInit {
  loading = false;
  loadingBatches = false;
  beers: Beer[] = [];
  filteredBeers: Beer[] = [];
  beerBatches: Record<string, Batch[]> = {};
  processing = false;
  adding = false;
  editing = false;
  addingBatch = false;
  editingBatch = false;
  showArchivedBatches = false;
  modifyBeer: Beer = new Beer();
  selectedBatchBeer: Beer = new Beer();
  modifyBatch: Batch = new Batch();
  isNilOrEmpty = isNilOrEmpty;
  imageTransitionsToDelete: string[] = [];
  locations: Location[] = [];
  selectedLocationFilters: string[] = [];
  _ = _;

  transformFns = beerTransformFns;

  externalBrewingTools: string[] = ['brewfather'];

  userInfo!: UserInfo;

  get displayedColumns() {
    return [
      'name',
      'description',
      'batchCount',
      'tapped',
      'externalBrewingTool',
      'style',
      'abv',
      'ibu',
      'srm',
      'untappdId',
      'imgUrl',
      'actions',
    ];
  }

  get displayedBatchColumns() {
    const cols: string[] = ['batchNumber', 'name', 'tapped'];

    if (!isNilOrEmpty(this.locations) && this.locations.length > 1) {
      cols.push('locations');
    }

    return _.concat(cols, [
      'externalBrewingTool',
      'abv',
      'ibu',
      'srm',
      'brewDate',
      'kegDate',
      'imgUrl',
      'actions',
    ]);
  }

  decimalRegex = /^-?\d*[.]?\d{0,2}$/;
  decimalValidator = Validators.pattern(this.decimalRegex);

  requiredIfNoBrewTool(comp: ManageBeerComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const brewTool = _.get(comp.modifyBeer.editValues, 'externalBrewingTool');
      if (!_.isEmpty(brewTool) && brewTool !== '-1') {
        return null;
      }

      if (isNilOrEmpty(control.value)) {
        return { requiredIfNoToolSelected: true };
      }

      return null;
    };
  }

  requiredForBatchIfNoBrewTool(comp: ManageBeerComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const brewTool = _.get(comp.modifyBatch.editValues, 'externalBrewingTool');
      if (!_.isEmpty(brewTool) && brewTool !== '-1') {
        return null;
      }

      if (isNilOrEmpty(control.value)) {
        return { requiredIfNoToolSelected: true };
      }

      return null;
    };
  }

  requiredForBrewingTool(comp: ManageBeerComponent, tool: string): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const brewTool = _.get(comp.modifyBeer.editValues, 'externalBrewingTool');
      if (_.isEmpty(brewTool) || brewTool === '-1') {
        return null;
      }

      if (brewTool === tool && (_.isNil(control.value) || _.isEmpty(control.value))) {
        return { requiredForBrewTool: true };
      }

      return null;
    };
  }

  requiredForBatchForBrewingTool(comp: ManageBeerComponent, tool: string): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const brewTool = _.get(comp.modifyBatch.editValues, 'externalBrewingTool');
      if (_.isEmpty(brewTool) || brewTool === '-1') {
        return null;
      }

      if (brewTool === tool && (_.isNil(control.value) || _.isEmpty(control.value))) {
        return { requiredForBrewTool: true };
      }

      return null;
    };
  }

  requiredIfImageTransitionsEnabled(comp: ManageBeerComponent): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const imageTransitionsEnabled = _.get(comp.modifyBeer.editValues, 'imageTransitionsEnabled');

      if (!imageTransitionsEnabled) {
        return null;
      }

      if (isNilOrEmpty(control.value)) {
        return { requiredIfImageTransitionsEnabled: true };
      }

      return null;
    };
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
    brewfatherRecipeId: new UntypedFormControl('', [
      this.requiredForBrewingTool(this, 'brewfather'),
    ]),
    untappdId: new UntypedFormControl(''),
  });

  modifyBatchFormGroup: UntypedFormGroup = new UntypedFormGroup({
    batchNumber: new UntypedFormControl('', [this.requiredForBatchIfNoBrewTool(this)]),
    locationIds: new UntypedFormControl('', [Validators.required]),
    abv: new UntypedFormControl('', [this.decimalValidator]),
    srm: new UntypedFormControl('', [this.decimalValidator]),
    ibu: new UntypedFormControl('', [this.decimalValidator]),
    name: new UntypedFormControl('', []),
    externalBrewingTool: new UntypedFormControl(-1),
    brewfatherBatchId: new UntypedFormControl('', [
      this.requiredForBatchForBrewingTool(this, 'brewfather'),
    ]),
    brewDate: new UntypedFormControl(new Date(), [this.requiredForBatchIfNoBrewTool(this)]),
    kegDate: new UntypedFormControl(new Date(), [this.requiredForBatchIfNoBrewTool(this)]),
    imgUrl: new UntypedFormControl('', []),
  });

  constructor(
    private currentUserService: CurrentUserService,
    private dataService: DataService,
    private router: Router,
    private _snackBar: MatSnackBar,
    public dialog: MatDialog
  ) {}

  @ViewChild(MatSort) sort!: MatSort;

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  _refresh(always?: () => void, next?: () => void, error?: (err: DataError) => void) {
    this.dataService.getLocations().subscribe({
      next: (locations: Location[]) => {
        this.locations = [];
        for (const location of _.sortBy(locations, [
          (l: Location) => {
            return l.description;
          },
        ])) {
          this.locations.push(new Location(location));
        }
        this.dataService.getBeers().subscribe({
          next: (beers: Beer[]) => {
            this.beers = [];
            _.forEach(beers, _beer => {
              const beer = new Beer(_beer);
              this.beers.push(beer);
              this.beerBatches[beer.id] = [];
              this.dataService.getBeerBatches(beer.id, true, this.showArchivedBatches).subscribe({
                next: (batches: Batch[]) => {
                  _.forEach(batches, _batch => {
                    const batch = new Batch(_batch);
                    this.beerBatches[beer.id].push(batch);
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
                complete: () => {
                  if (!_.isNil(next)) {
                    next();
                  }
                  if (!_.isNil(always)) {
                    always();
                  }
                },
              });
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
        this._refresh(() => {
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

    this._refresh(() => {
      this.loading = false;
    });
  }

  addBeer(): void {
    this.modifyBeerFormGroup.reset();
    const data: any = {};
    if (this.locations.length === 1) {
      data['locationId'] = this.locations[0].id;
    }
    this.modifyBeer = new Beer(data);
    this.modifyBeer.editValues = data;
    this.adding = true;
  }

  createBeer(): void {
    const data: any = {};
    const keys = [
      'name',
      'description',
      'externalBrewingTool',
      'style',
      'abv',
      'ibu',
      'srm',
      'imgUrl',
      'externalBrewingToolMeta',
      'emptyImgUrl',
      'imageTransitionsEnabled',
    ];
    const checkKeys = {};

    _.forEach(keys, k => {
      const checkKey: any = _.get(checkKeys, k, k);

      let val: any = _.get(this.modifyBeer.editValues, checkKey);
      if (isNilOrEmpty(val)) {
        return;
      }
      const transformFn: any = _.get(this.transformFns, k);
      if (!_.isNil(transformFn) && typeof transformFn === 'function') {
        val = transformFn(val);
      }
      data[k] = val;
    });

    if (this.modifyBeer.imageTransitions) {
      const imageTransitions: any[] = [];
      for (const i of this.modifyBeer.imageTransitions) {
        imageTransitions.push({
          changePercent: i.editValues.changePercent,
          imgUrl: i.editValues.imgUrl,
        });
      }
      if (imageTransitions) {
        data['imageTransitions'] = imageTransitions;
      }
    }

    if (_.has(data, 'externalBrewingTool')) {
      const tool = data['externalBrewingTool'];
      if (isNilOrEmpty(tool)) {
        delete data['externalBrewingTool'];
      }
    }

    if (_.has(data, 'externalBrewingToolMeta')) {
      if (isNilOrEmpty(_.get(data, 'externalBrewingTool'))) {
        delete data['externalBrewingToolMeta'];
      }
    }

    this.processing = true;
    this.dataService.createBeer(data).subscribe({
      next: (beer: Beer) => {
        const _beer = new Beer(beer);
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
      },
    });
  }

  cancelAddBeer(): void {
    this.adding = false;
  }

  editBeer(beer: Beer, refresh = true): void {
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
    if (_.isEmpty(this.imageTransitionsToDelete)) {
      this.saveBeerActual();
    } else {
      const imageTransitionId = this.imageTransitionsToDelete.pop();
      if (!imageTransitionId) {
        return this.saveBeerActual();
      }

      this.dataService.deleteImageTransition(imageTransitionId).subscribe({
        next: (_: any) => {
          this.deleteImageTransitionRecursive();
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        },
      });
    }
  }

  saveBeerActual(): void {
    if (isNilOrEmpty(this.beerChanges)) {
      this._refresh(
        () => {
          this.processing = false;
        },
        () => {
          this.editing = false;
        }
      );
    } else {
      this.dataService.updateBeer(this.modifyBeer.id, this.beerChanges).subscribe({
        next: (beer: Beer) => {
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
  }

  cancelEditBeer(): void {
    this.modifyBeer.disableEditing();
    if (!isNilOrEmpty(this.imageTransitionsToDelete)) {
      this._refresh(
        () => {
          this.processing = false;
        },
        () => {
          this.editing = false;
        }
      );
    } else {
      this.editing = false;
    }
  }

  deleteBeer(beer: Beer): void {
    if (confirm(`Are you sure you want to delete beer '${beer.getName()}'?`)) {
      this.processing = true;
      const tapIds = this.beerBatchesAssocTaps(beer);
      if (!isNilOrEmpty(tapIds)) {
        if (
          confirm(
            `The beer has 1 or more batch associated with one or more taps.  Batches must first be cleared from the tap(s) before deleting. Proceed?`
          )
        ) {
          this.clearNextTap(
            tapIds,
            () => {
              this._deleteBeer(beer);
            },
            (err: DataError) => {
              this.displayError(err.message);
              this.processing = false;
            }
          );
        }
      } else {
        this._deleteBeer(beer);
      }
    }
  }

  beerBatchesAssocTaps(_: Beer): string[] {
    const tapIds: string[] = [];

    return tapIds;
  }

  clearNextTap(tapIds: string[], next: () => void, error: (err: DataError) => void): void {
    if (isNilOrEmpty(tapIds)) return next();

    const tapId = tapIds.pop();
    if (!tapId) return next();

    this.clearTap(
      tapId,
      () => {
        this.clearNextTap(tapIds, next, error);
      },
      error
    );
  }

  clearTap(tapId: string, next: () => void, error: (err: DataError) => void): void {
    this.dataService.clearTap(tapId).subscribe({
      next: (_: any) => {
        next();
      },
      error: (err: DataError) => {
        error(err);
      },
    });
  }

  _deleteBeer(beer: Beer): void {
    this.processing = true;
    this.dataService.deleteBeer(beer.id).subscribe({
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

  filter(sort?: Sort) {
    let sortBy = 'description';
    let asc = true;

    if (!_.isNil(sort) && !_.isEmpty(this.sort.active) && !_.isEmpty(this.sort.direction)) {
      sortBy = this.sort.active;
      asc = this.sort.direction == 'asc';
    }

    let filteredData: Beer[] = this.beers;

    filteredData = _.sortBy(filteredData, [
      (d: Beer) => {
        if (sortBy === 'name') {
          return d.getName();
        }

        if (sortBy === 'description') {
          return d.getDescription();
        }

        if (sortBy === 'style') {
          return d.getStyle();
        }

        if (sortBy === 'abv') {
          return d.getAbv();
        }

        if (sortBy === 'ibu') {
          return d.getIbu();
        }

        if (sortBy === 'srm') {
          return d.getSrm();
        }
        return _.get(d, sortBy);
      },
    ]);
    if (!asc) {
      _.reverse(filteredData);
    }
    this.filteredBeers = filteredData;
  }

  beerBrewToolChanges(_?: any) {
    this.addMissingBeerMeta();
    this.reRunBeerValidation();
  }

  addMissingBeerMeta() {
    switch (this.modifyBeer.editValues.externalBrewingTool) {
      case 'brewfather':
        if (!_.has(this.modifyBeer.editValues.externalBrewingToolMeta, 'recipeId')) {
          _.set(this.modifyBeer.editValues, 'externalBrewingToolMeta.recipeId', '');
        }
        break;
    }
  }

  get modifyBeerForm(): Record<string, AbstractControl> {
    return this.modifyBeerFormGroup.controls;
  }

  reRunBeerValidation(): void {
    _.forEach(this.modifyBeerForm, ctrl => {
      ctrl.updateValueAndValidity();
    });
  }

  get hasBeerChanges(): boolean {
    return !_.isEmpty(this.beerChanges) || !isNilOrEmpty(this.imageTransitionsToDelete);
  }

  get beerChanges(): any {
    const changes = _.cloneDeep(this.modifyBeer.changes);

    if (_.get(changes, 'externalBrewingTool') === '-1') {
      changes['externalBrewingTool'] = null;
      changes['externalBrewingToolMeta'] = null;
    } else {
      if (_.has(changes, 'externalBrewingToolMeta')) {
        if (isNilOrEmpty(_.get(this.modifyBeer, 'externalBrewingTool'))) {
          delete changes['externalBrewingToolMeta'];
        }
      }
    }

    if (_.has(_.get(changes, 'externalBrewingToolMeta', {}), 'details')) {
      delete changes['externalBrewingToolMeta']['details'];
    }

    if (_.has(changes, 'imageTransitions') && this.modifyBeer.imageTransitions) {
      const imageTransitions: ImageTransition[] = [];
      for (const i of this.modifyBeer.imageTransitions) {
        if (i.hasChanges) {
          imageTransitions.push({ id: i.id, ...i.changes });
        }
      }
      if (isNilOrEmpty(imageTransitions)) {
        delete changes['imageTransitions'];
      } else {
        changes['imageTransitions'] = imageTransitions;
      }
    }

    const keys = ['name', 'description', 'style', 'abv', 'ibu', 'srm', 'imgUrl'];
    _.forEach(keys, k => {
      if (_.has(changes, k)) {
        if (isNilOrEmpty(changes[k])) {
          changes[k] = null;
        }
      }
    });
    return changes;
  }

  openUploadDialog(targetObj: any, key: string): void {
    const dialogRef = this.dialog.open(FileUploadDialogComponent, {
      data: {
        imageType: 'beer',
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
        imageType: 'beer',
      },
    });

    dialogRef.afterClosed().subscribe(result => {
      if (!isNilOrEmpty(result)) {
        _.set(targetObj, key, result);
      }
    });
  }

  openImagePreviewDialog(imgUrl: string): void {
    this.dialog.open(LocationImageDialogComponent, {
      data: {
        imgUrl: imgUrl,
      },
    });
  }

  getBeerLink(beer: Beer): string {
    if (_.isNil(beer)) return '';

    const recipeId = _.get(beer.externalBrewingToolMeta, 'recipeId');
    if (
      beer.externalBrewingTool === 'brewfather' &&
      beer.externalBrewingToolMeta &&
      !isNilOrEmpty(recipeId)
    ) {
      return `https://web.brewfather.app/tabs/recipes/recipe/${recipeId}`;
    }

    return '';
  }

  getBatchLink(batch: Batch): string {
    if (_.isNil(batch)) return '';

    const batchId = _.get(batch.externalBrewingToolMeta, 'batchId');
    if (
      batch.externalBrewingTool === 'brewfather' &&
      batch.externalBrewingToolMeta &&
      !isNilOrEmpty(batchId)
    ) {
      return `https://web.brewfather.app/tabs/batches/batch/${batchId}`;
    }

    return '';
  }

  isBeerTapped(beer: Beer): boolean {
    let isTapped = false;
    _.forEach(this.beerBatches[beer.id], batch => {
      if (!isNilOrEmpty(batch.taps)) {
        isTapped = true;
      }
    });
    return isTapped;
  }

  beerAssocTaps(beer: Beer): Tap[] {
    const tapIds: Tap[] = [];

    _.forEach(this.beerBatches[beer.id], batch => {
      if (!isNilOrEmpty(batch.taps)) {
        _.forEach(batch.taps, tap => {
          tapIds.push(tap);
        });
      }
    });
    return tapIds;
  }

  isBatchTapped(batch: Batch): boolean {
    return !isNilOrEmpty(batch.taps);
  }

  addImageTransition(): void {
    if (!this.modifyBeer.imageTransitions) {
      this.modifyBeer.imageTransitions = [];
    }
    const i = new ImageTransition();
    i.enableEditing();
    this.modifyBeer.imageTransitions.push(i);
  }

  get areImageTransitionsValid(): boolean {
    if (
      _.isNil(this.modifyBeer.editValues) ||
      _.isNil(this.modifyBeer.imageTransitions) ||
      !this.modifyBeer.imageTransitionsEnabled
    ) {
      return true;
    }

    for (const imageTransition of this.modifyBeer.imageTransitions) {
      if (
        isNilOrEmpty(imageTransition.editValues.changePercent) ||
        isNilOrEmpty(imageTransition.editValues.imgUrl) ||
        imageTransition.editValues.changePercent < 1 ||
        imageTransition.editValues.changePercent > 99
      ) {
        return false;
      }
    }

    return true;
  }

  removeImageTransitionItemFromList(imageTransition: ImageTransition): void {
    if (!isNilOrEmpty(imageTransition.id)) {
      return this.removeImageTransitionItemFromListById(imageTransition);
    }

    if (
      isNilOrEmpty(imageTransition) ||
      isNilOrEmpty(this.modifyBeer) ||
      !this.modifyBeer.imageTransitions
    ) {
      return;
    }

    const changePercent = imageTransition.isEditing
      ? imageTransition.editValues.changePercent
      : imageTransition.editValues;
    const imgUrl = imageTransition.isEditing
      ? imageTransition.editValues.imgUrl
      : imageTransition.imgUrl;
    const list: ImageTransition[] = [];
    for (const i of this.modifyBeer.imageTransitions) {
      const _changePercent = i.isEditing ? i.editValues.changePercent : i.editValues;
      const _imgUrl = i.isEditing ? i.editValues.imgUrl : i.imgUrl;
      if (_changePercent !== changePercent && _imgUrl !== imgUrl) {
        list.push(i);
      }
    }
    this.modifyBeer.imageTransitions = list;
  }

  removeImageTransitionItemFromListById(imageTransition: ImageTransition): void {
    if (
      isNilOrEmpty(imageTransition) ||
      isNilOrEmpty(imageTransition.id) ||
      isNilOrEmpty(this.modifyBeer) ||
      !this.modifyBeer.imageTransitions
    ) {
      return;
    }

    const list: ImageTransition[] = [];
    for (const i of this.modifyBeer.imageTransitions) {
      if (i.id !== imageTransition.id) {
        list.push(i);
      }
    }
    this.modifyBeer.imageTransitions = list;
    this.imageTransitionsToDelete.push(imageTransition.id);
  }

  getDescriptionDisplay(beer: Beer): string {
    const desc = beer.getDescription();

    if (isNilOrEmpty(desc)) {
      return '';
    }
    if (this.isDescriptionTooLong(beer)) {
      return _.truncate(desc, { length: 48 });
    }
    return desc;
  }

  isDescriptionTooLong(beer: Beer): boolean {
    const desc = beer.getDescription();

    if (isNilOrEmpty(desc)) {
      return false;
    }
    if (_.size(desc) > 48) {
      return true;
    }
    return false;
  }

  batchBrewToolChanges(_?: any) {
    this.addMissingBatchMeta();
    this.reRunBatchValidation();
  }

  addMissingBatchMeta() {
    switch (this.modifyBatch.editValues.externalBrewingTool) {
      case 'brewfather':
        if (!_.has(this.modifyBatch.editValues.externalBrewingToolMeta, 'batchId')) {
          _.set(this.modifyBatch.editValues, 'externalBrewingToolMeta.batchId', '');
        }
        break;
    }
  }

  get modifyBatchForm(): Record<string, AbstractControl> {
    return this.modifyBatchFormGroup.controls;
  }

  reRunBatchValidation(): void {
    _.forEach(this.modifyBatchForm, ctrl => {
      ctrl.updateValueAndValidity();
    });
  }

  get hasBatchChanges(): boolean {
    return !_.isEmpty(this.batchChanges);
  }

  get batchChanges(): any {
    const changes = _.cloneDeep(this.modifyBatch.changes);

    if (_.get(changes, 'externalBrewingTool') === '-1') {
      changes['externalBrewingTool'] = null;
      changes['externalBrewingToolMeta'] = null;
    } else {
      if (_.has(changes, 'externalBrewingToolMeta')) {
        if (isNilOrEmpty(_.get(this.modifyBatch, 'externalBrewingTool'))) {
          delete changes['externalBrewingToolMeta'];
        }
      }
    }

    const keys = ['batchNumber', 'abv', 'ibu', 'srm', 'kegDate', 'brewDate'];
    _.forEach(keys, k => {
      if (_.has(changes, k)) {
        if (isNilOrEmpty(changes[k])) {
          changes[k] = null;
        }
      }
    });
    return changes;
  }

  addBatch(beer: Beer): void {
    this.selectedBatchBeer = beer;
    this.modifyBatchFormGroup.reset();
    const data: any = {};
    if (this.locations.length == 1) {
      data['locationIds'] = [this.locations[0].id];
    }
    this.modifyBatch = new Batch(data);
    this.modifyBatch.editValues = data;
    this.addingBatch = true;
  }

  createBatch(): void {
    const data: any = { beerId: this.selectedBatchBeer.id };
    const keys = [
      'externalBrewingTool',
      'abv',
      'ibu',
      'srm',
      'externalBrewingToolMeta',
      'batchNumber',
      'name',
      'imgUrl',
      'locationIds',
    ];
    const dateKeys = ['brewDateObj', 'kegDateObj'];
    const checkKeys = {};

    _.forEach(keys, k => {
      const checkKey: any = _.get(checkKeys, k, k);

      let val: any = _.get(this.modifyBatch.editValues, checkKey);
      if (isNilOrEmpty(val)) {
        return;
      }
      const transformFn: any = _.get(this.transformFns, k);
      if (!_.isNil(transformFn) && typeof transformFn === 'function') {
        val = transformFn(val);
      }
      data[k] = val;
    });

    _.forEach(dateKeys, k => {
      const _k = k.replace('Obj', '');

      let val: any = _.get(this.modifyBatch.editValues, k);
      if (isNilOrEmpty(val)) {
        return;
      }

      val = toUnixTimestamp(val);
      const transformFn: any = _.get(this.transformFns, _k);
      if (!_.isNil(transformFn) && typeof transformFn === 'function') {
        val = transformFn(val);
      }
      data[_k] = val;
    });

    if (_.has(data, 'externalBrewingTool')) {
      const tool = data['externalBrewingTool'];
      if (isNilOrEmpty(tool)) {
        delete data['externalBrewingTool'];
      }
    }

    if (_.has(data, 'externalBrewingToolMeta')) {
      if (isNilOrEmpty(_.get(data, 'externalBrewingTool'))) {
        delete data['externalBrewingToolMeta'];
      }
    }

    this.processing = true;
    this.dataService.createBatch(data).subscribe({
      next: (_: Batch) => {
        this._refresh(
          () => {
            this.processing = false;
          },
          () => {
            this.addingBatch = false;
          }
        );
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      },
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
    const changes = this.batchChanges;

    if (isNilOrEmpty(changes)) {
      this._refresh(
        () => {
          this.processing = false;
        },
        () => {
          this.editingBatch = false;
        }
      );
      return;
    }

    const affectedTaps = this._getAffectedTaps(changes);
    if (!_.isEmpty(affectedTaps)) {
      const tapDescriptions = affectedTaps
        .map(t => `Tap #${t.tapNumber} (${t.description})`)
        .join(', ');
      if (
        !confirm(
          `The following taps are at locations being removed from this batch and will be disconnected: ${tapDescriptions}. Continue?`
        )
      ) {
        this.processing = false;
        return;
      }

      this._processAffectedTaps(affectedTaps, 0, () => {
        this._executeSaveBatch(changes);
      });
      return;
    }

    this._executeSaveBatch(changes);
  }

  private _getAffectedTaps(changes: any): Tap[] {
    if (!changes.locationIds || isNilOrEmpty(this.modifyBatch.taps)) {
      return [];
    }

    const newLocationIds: string[] = changes.locationIds;
    const removedLocationIds = (this.modifyBatch.locationIds || []).filter(
      (id: string) => !newLocationIds.includes(id)
    );

    if (_.isEmpty(removedLocationIds)) {
      return [];
    }

    return this.modifyBatch.taps!.filter((tap: Tap) => removedLocationIds.includes(tap.locationId));
  }

  private _processAffectedTaps(taps: Tap[], index: number, next: () => void): void {
    if (index >= taps.length) {
      next();
      return;
    }

    const tap = taps[index];

    const proceedAfterKegtron = () => {
      this.dataService.clearTap(tap.id).subscribe({
        next: () => {
          this._processAffectedTaps(taps, index + 1, next);
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        },
      });
    };

    const meta = tap.tapMonitor?.meta;
    const hasKegtronMeta =
      meta != null && meta.deviceId != null && typeof meta.portNum === 'number';
    if (tap.tapMonitor?.monitorType === 'kegtron-pro' && hasKegtronMeta) {
      this.dataService.clearKegtronPort(meta!.deviceId, meta!.portNum).subscribe({
        next: () => {
          proceedAfterKegtron();
        },
        error: (err: DataError) => {
          this.displayError(
            'There was an error trying to clear the Kegtron port, skipping...  Error: ' +
              err.message
          );
          proceedAfterKegtron();
        },
      });
    } else {
      proceedAfterKegtron();
    }
  }

  private _executeSaveBatch(changes: any): void {
    this.dataService.updateBatch(this.modifyBatch.id, changes).subscribe({
      next: (_: Batch) => {
        this._refresh(
          () => {
            this.processing = false;
          },
          () => {
            this.editingBatch = false;
          }
        );
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      },
    });
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
        if (confirm(`Are you sure you want to archive the batch keg'd on ${batch.getKegDate()}?`)) {
          if (!_.isNil(batch.taps) && batch.taps.length > 0) {
            const tapIds: string[] = [];
            _.forEach(batch.taps, tap => {
              tapIds.push(tap.id);
            });
            if (
              confirm(
                `The batch is associated with one or more taps.  It will need to be cleared from tap(s) before archiving.  Proceed?`
              )
            ) {
              this.clearNextTap(
                tapIds,
                () => {
                  this._archiveBatch(batch);
                },
                (err: DataError) => {
                  this.displayError(err.message);
                  this.processing = false;
                }
              );
            }
          } else {
            this._archiveBatch(batch);
          }
        }
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      },
    });
  }

  _archiveBatch(batch: Batch): void {
    this.processing = true;
    this.loadingBatches = true;
    this.dataService
      .updateBatch(batch.id, { archivedOn: convertUnixTimestamp(Date.now()) })
      .subscribe({
        next: (_: any) => {
          this.processing = false;
          this.loading = true;
          this._refresh(() => {
            this.loading = false;
            this.loadingBatches = false;
          });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
          this.loadingBatches = false;
        },
      });
  }

  unarchiveBatch(batch: Batch): void {
    if (confirm(`Are you sure you want to unarchive the batch keg'd on ${batch.getKegDate()}?`)) {
      this.processing = true;
      this.loadingBatches = true;
      this.dataService.updateBatch(batch.id, { archivedOn: null }).subscribe({
        next: (_: any) => {
          this.processing = false;
          this.loading = true;
          this._refresh(() => {
            this.loading = false;
            this.loadingBatches = false;
          });
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
          this.loadingBatches = false;
        },
      });
    }
  }

  toggleArchivedBatches(): void {
    this.loadingBatches = true;
    if (this.editing && this.modifyBeer && this.modifyBeer.id) {
      this.dataService
        .getBeerBatches(this.modifyBeer.id, true, this.showArchivedBatches)
        .subscribe({
          next: (batches: Batch[]) => {
            this.beerBatches[this.modifyBeer.id] = [];
            _.forEach(batches, _batch => {
              this.beerBatches[this.modifyBeer.id].push(new Batch(_batch));
            });
            this.loadingBatches = false;
          },
          error: (err: DataError) => {
            this.displayError(err.message);
            this.loadingBatches = false;
          },
        });
    }
  }

  isArchivedBatch(batch: Batch): boolean {
    return !isNilOrEmpty(batch.archivedOn);
  }
}
