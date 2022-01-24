import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { DataService } from '../../data.service';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, Sort} from '@angular/material/sort';
import { FormControl, AbstractControl, Validators, FormGroup } from '@angular/forms';

import { Beer, DataError, Location } from '../../models/models';

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
  _ = _;

  externalBrewingTool!: string;
  style!: number;
  abv!: string;
  imgUrl!: string;
  ibu!: number;
  kegDate!: string;
  brewDate!: string;
  srm!: number;

  modifyFormGroup: FormGroup = new FormGroup({
    // name: new FormControl('', [Validators.required]),
    // locationId: new FormControl('', [Validators.required]),
    // metaAuthToken: new FormControl('', [Validators.required])
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
    console.log(this.modifyBeer);
    this.processing = true;
    var data: any = {
      name: this.modifyBeer.editValues.name,
  // description!: string;
  // externalBrewingTool!: string;
  // externalBrewingToolMeta!: Object;
  // style!: number;
  // abv!: string;
  // imgUrl!: string;
  // ibu!: number;
  // kegDate!: string;
  // brewDate!: string;
  // srm!: number;
    }
    console.log(data)
    // this.dataService.createBeer(data).subscribe({
    //   next: (beer: Beer) => {
    //     this.refresh(() => {this.processing = false;}, () => {this.adding = false;});
    //   },
    //   error: (err: DataError) => {
    //     this.displayError(err.message);
    //     this.processing = false;
    //   }
    // })
  }

  cancelAdd(): void {
    this.adding = false;
  }

  edit(beer: Beer): void {
    beer.enableEditing();
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

  addMissingMeta() {
    // switch(this.modifySensor.editValues.sensorType) {
    //   case "plaato-keg":
    //     if(!_.has(this.modifySensor.editValues.meta, "authToken")){
    //       console.log("adding missing metadata");
    //       console.log(this.modifySensor.editValues.meta)
    //       _.set(this.modifySensor.editValues, 'meta.authToken', '');
    //       console.log(this.modifySensor);
    //     }
    //     break
    // }
  }

  get modifyForm(): { [key: string]: AbstractControl } {
    return this.modifyFormGroup.controls;
  } 
}
