import { Component, OnInit } from '@angular/core';
import { FormControl, AbstractControl, ValidatorFn, ValidationErrors, Validators, FormGroup } from '@angular/forms';

import { isNilOrEmpty } from '../../utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-volume-calculator',
  templateUrl: './volume-calculator.component.html',
  styleUrls: ['./volume-calculator.component.scss']
})
export class VolumeCalculatorComponent implements OnInit {

  decimalRegex = /^-?\d*[.]?\d{0,3}$/;
  decimalValidator = Validators.pattern(this.decimalRegex); 

  requiredIfCalcType(comp: VolumeCalculatorComponent, type: String): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null  => {
      var selectedType = comp.calType;
      if(selectedType !== type) {
        return null;
      }
      
      if(isNilOrEmpty(control.value)) {
        return { required: true };
      }

      return null;
    }
  }

  volCalcFormGroup: FormGroup = new FormGroup({
    totalWeight: new FormControl('', [this.requiredIfCalcType(this, "byWeight"), this.decimalValidator]),
    totalWeightUnit: new FormControl('kg', [Validators.required]),
    targetVolume: new FormControl('', [this.requiredIfCalcType(this, "byVolume"), this.decimalValidator]),
    targetVolumeUnit: new FormControl('gal', [Validators.required]),
    emptyContainerWeight: new FormControl('', [Validators.required, this.decimalValidator]),
    emptyContainerWeightUnit: new FormControl('kg', [Validators.required]),
    gravity: new FormControl('', [Validators.required, this.decimalValidator]),
    gravityUnit: new FormControl('sg', [Validators.required]),
  });

  calType: String = "byWeight"
  resultsG: number = 0;
  resultsL: number = 0;
  resultsLbs: number = 0;
  resultsKgs: number = 0;

  isNilOrEmpty: Function = isNilOrEmpty;
  _ = _;

  constructor() { }

  ngOnInit(): void {
  }

  lbs2Kgs(lbs: number): number {
    return lbs * 0.45359237;
  }

  kgs2Lbs(kgs: number): number {
    return kgs * 2.2046226218;
  }

  calculate(): void {
    console.log(this.volCalcFormGroup.value);
    let totalWeightVal = _.toNumber(this.volCalcFormGroup.value.totalWeight);
    let targetVolumeVal = _.toNumber(this.volCalcFormGroup.value.targetVolume);
    let emptyContainerWeightVal = _.toNumber(this.volCalcFormGroup.value.emptyContainerWeight);
    let gravityVal = _.toNumber(this.volCalcFormGroup.value.gravity);

    if (this.volCalcFormGroup.value.totalWeightUnit === "lbs") {
      console.log("Total weight unit is in lbs.  Converting to kgs.  Current value: " + totalWeightVal + " (lbs)");
      totalWeightVal = this.lbs2Kgs(totalWeightVal);
      console.log("New total weight value: " + totalWeightVal + " (kgs)");
    }
    
    if (this.volCalcFormGroup.value.targetVolumeUnit === "gal") {
      console.log("Target volume unit is in gal.  Converting to liters.  Current value: " + targetVolumeVal + " (gal)");
      targetVolumeVal = targetVolumeVal * 3.785411784;
      console.log("New target volume value: " + targetVolumeVal + " (liters)");
    }

    if (this.volCalcFormGroup.value.emptyContainerWeightUnit == "lbs") {
      console.log("Empty container weight unit is in lbs.  Converting to kgs.  Current value: " + emptyContainerWeightVal + " (lbs)");
      emptyContainerWeightVal = this.lbs2Kgs(emptyContainerWeightVal);
      console.log("New empty container weight value: " + emptyContainerWeightVal + " (kgs)");
    }

    if (this.volCalcFormGroup.value.gravityUnit === "plato") {
      console.log("Gravity unit is in plato.  Converting to SG.  Current value: " + gravityVal + " (plato)");
      gravityVal = 1 + (gravityVal / (258.6 - ((gravityVal/258.2)*227.1)));
      console.log("New gravity value: " + gravityVal + " (SG)");
    }

    if(this.calType === 'byWeight') {
      this.calcVolume(totalWeightVal, emptyContainerWeightVal, gravityVal);
    }

    if(this.calType === 'byVolume') {
      this.calcWeight(targetVolumeVal, emptyContainerWeightVal, gravityVal);
    }
  }

  calcVolume(totalWeightKg:number, emptyContainerWeightKg:number, gravitySG:number): void {
    const weightOfCO2Kg = 0; //TODO 
    const liquidWeight = (totalWeightKg - weightOfCO2Kg) - emptyContainerWeightKg;
    const specificWeight = liquidWeight / gravitySG;
    
    this.resultsL = specificWeight;
    this.resultsG = specificWeight * 0.264172; // convert Liter to gal
    console.log("Liters: " + this.resultsL);
    console.log("Gallons: " + this.resultsG);
  }

  calcWeight(targetVolumeL:number, emptyContainerWeightKg:number, gravitySG:number): void {
    const liquidWeight = (gravitySG * targetVolumeL);
    console.log("Liquid weight: " + liquidWeight + " (" + gravitySG + " * " + targetVolumeL + ")")
    const weight = liquidWeight + emptyContainerWeightKg;
    console.log("Weight: " + weight + " (" + liquidWeight + " + " + emptyContainerWeightKg + ")")

    this.resultsKgs = weight;
    this.resultsLbs = this.kgs2Lbs(weight);
    console.log("kgs: " + this.resultsKgs);
    console.log("lbs: " + this.resultsLbs);
  }

  reset(data?: any): void {
    if(isNilOrEmpty(data)) {
      data = {
        totalWeightUnit: 'kg',
        targetVolumeUnit: 'gal',
        emptyContainerWeightUnit: 'kg',
        gravityUnit: 'sg',
        liquidTemperatureUnit: 'f',
        pressure: 0,
        pressureUnit: "psi",
      };
    }

    this.volCalcFormGroup.reset(data);
  
    this.resultsG = 0;
    this.resultsL = 0;
  }

  calTypeChanged(): void {
    this.reset(this.volCalcFormGroup.value);
  }

  get volCalcForm(): { [key: string]: AbstractControl } {
    return this.volCalcFormGroup.controls;
  } 

}
