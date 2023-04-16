import { Component, OnInit } from '@angular/core';
import { UntypedFormControl, AbstractControl, ValidatorFn, ValidationErrors, Validators, UntypedFormGroup } from '@angular/forms';

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

  volCalcFormGroup: UntypedFormGroup = new UntypedFormGroup({
    totalWeight: new UntypedFormControl('', [this.requiredIfCalcType(this, "byWeight"), this.decimalValidator]),
    totalWeightUnit: new UntypedFormControl('kg', [Validators.required]),
    targetVolume: new UntypedFormControl('', [this.requiredIfCalcType(this, "byVolume"), this.decimalValidator]),
    targetVolumeUnit: new UntypedFormControl('gal', [Validators.required]),
    emptyContainerWeight: new UntypedFormControl('', [Validators.required, this.decimalValidator]),
    emptyContainerWeightUnit: new UntypedFormControl('kg', [Validators.required]),
    gravity: new UntypedFormControl('', [Validators.required, this.decimalValidator]),
    gravityUnit: new UntypedFormControl('sg', [Validators.required]),
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
    let totalWeightVal = _.toNumber(this.volCalcFormGroup.value.totalWeight);
    let targetVolumeVal = _.toNumber(this.volCalcFormGroup.value.targetVolume);
    let emptyContainerWeightVal = _.toNumber(this.volCalcFormGroup.value.emptyContainerWeight);
    let gravityVal = _.toNumber(this.volCalcFormGroup.value.gravity);

    if (this.volCalcFormGroup.value.totalWeightUnit === "lbs") {
      totalWeightVal = this.lbs2Kgs(totalWeightVal);
    }
    
    if (this.volCalcFormGroup.value.targetVolumeUnit === "gal") {
      targetVolumeVal = targetVolumeVal * 3.785411784;
    }

    if (this.volCalcFormGroup.value.emptyContainerWeightUnit == "lbs") {
      emptyContainerWeightVal = this.lbs2Kgs(emptyContainerWeightVal);
    }

    if (this.volCalcFormGroup.value.gravityUnit === "plato") {
      gravityVal = 1 + (gravityVal / (258.6 - ((gravityVal/258.2)*227.1)));
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
  }

  calcWeight(targetVolumeL:number, emptyContainerWeightKg:number, gravitySG:number): void {
    const liquidWeight = (gravitySG * targetVolumeL);
    const weight = liquidWeight + emptyContainerWeightKg;

    this.resultsKgs = weight;
    this.resultsLbs = this.kgs2Lbs(weight);
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
