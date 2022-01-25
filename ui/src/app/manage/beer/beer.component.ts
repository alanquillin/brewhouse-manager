import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService } from '../../data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { FormControl, AbstractControl, ValidatorFn, ValidationErrors, Validators, FormGroup } from '@angular/forms';

import { Beer, DataError, Location } from '../../models/models';
import { toUnixTimestamp } from '../..//utils/datetime';
import { isNilOrEmpty } from '../..//utils/helpers';


import * as _ from 'lodash';

@Component({
  selector: 'app-beer',
  templateUrl: './beer.component.html',
  styleUrls: ['./beer.component.scss']
})
export class ManageBeerComponent implements OnInit {

  beers: Beer[] = [];
  filteredBeers: Beer[] = [];
  displayedColumns: string[] = ['name', 'description', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', 'imgUrl', 'actions'];
  processing = false;
  adding = false;
  editing = false;
  modifyBeer: Beer = new Beer();
  isNilOrEmpty: Function = isNilOrEmpty;
  _ = _;

  transformFns = {
    abv: _.toNumber,
    ibu: _.toNumber,
    srm: _.toNumber,
    externalBrewingToolMeta: _.cloneDeep,
    brewDate: toUnixTimestamp,
    kegDate: toUnixTimestamp
  }

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
    brewfatherBatchId: new FormControl('', [this.requiredForBrewingTool(this, "brewfather")])
  });

  constructor(private dataService: DataService, private router: Router, private _snackBar: MatSnackBar) { }

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
    this.processing = true;
    this.refresh(()=> {
      this.processing = false;
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
    console.log(this.modifyBeer.editValues)
    const keys = ['name', 'description', 'externalBrewingTool', 'style', 'abv', 'ibu', 'srm', 'brewDate', 'kegDate', 'imgUrl', 'externalBrewingToolMeta']
    
    _.forEach(keys, (k) => {
      var val: any = _.get(this.modifyBeer.editValues, k);
      if(isNilOrEmpty(val)){
        return;
      }
      const transformFn = _.get(this.transformFns, k);
      if(!_.isNil(transformFn)){
        val = transformFn(val);
      }
      data[k] = val;
    })
    
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
    console.log(beer);
    this.modifyBeer = beer;
    this.editing = true;
    this.modifyFormGroup.reset();
  }

  save(): void {
    console.log(this.modifyBeer.editValues);
    this.processing = true;
    // this.dataService.updateBeer(this.modifyBeer.id, this.modifyBeer.changes).subscribe({
    //   next: (beer: Beer) => {
    //     this.modifyBeer.disableEditing();
    //     this.refresh(()=> {this.processing = false;}, () => {
    //       this.editing = false;
    //     })
    //   },
    //   error: (err: DataError) => {
    //     this.displayError(err.message);
    //     this.processing = false;
    //   }
    // })
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
          this.refresh(()=>{ this.processing = false; });
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
    filteredData = _.orderBy(filteredData, [sortBy], [asc])
    _.sortBy(filteredData, [(d: Beer) => {
        return _.get(sortBy, sortBy);
      }]);
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

}
