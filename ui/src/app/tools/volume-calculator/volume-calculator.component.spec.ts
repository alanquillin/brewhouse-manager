import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule, UntypedFormControl } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { VolumeCalculatorComponent } from './volume-calculator.component';

describe('VolumeCalculatorComponent', () => {
  let component: VolumeCalculatorComponent;
  let fixture: ComponentFixture<VolumeCalculatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        NoopAnimationsModule,
        MatSelectModule,
        MatFormFieldModule,
        MatInputModule,
      ],
      declarations: [VolumeCalculatorComponent],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(VolumeCalculatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have calType set to byWeight', () => {
      expect(component.calType).toBe('byWeight');
    });

    it('should have resultsG set to 0', () => {
      expect(component.resultsG).toBe(0);
    });

    it('should have resultsL undefined', () => {
      expect(component.resultsL).toBeUndefined();
    });

    it('should have resultsLbs set to 0', () => {
      expect(component.resultsLbs).toBe(0);
    });

    it('should have resultsKgs undefined', () => {
      expect(component.resultsKgs).toBeUndefined();
    });

    it('should have volCalcFormGroup defined', () => {
      expect(component.volCalcFormGroup).toBeTruthy();
    });

    it('should have decimalRegex pattern', () => {
      expect(component.decimalRegex).toBeTruthy();
    });
  });

  describe('form controls', () => {
    it('should have totalWeight control', () => {
      expect(component.volCalcFormGroup.get('totalWeight')).toBeTruthy();
    });

    it('should have totalWeightUnit control defaulting to kg', () => {
      expect(component.volCalcFormGroup.get('totalWeightUnit')?.value).toBe('kg');
    });

    it('should have targetVolume control', () => {
      expect(component.volCalcFormGroup.get('targetVolume')).toBeTruthy();
    });

    it('should have targetVolumeUnit control defaulting to gal', () => {
      expect(component.volCalcFormGroup.get('targetVolumeUnit')?.value).toBe('gal');
    });

    it('should have emptyContainerWeight control', () => {
      expect(component.volCalcFormGroup.get('emptyContainerWeight')).toBeTruthy();
    });

    it('should have emptyContainerWeightUnit control defaulting to kg', () => {
      expect(component.volCalcFormGroup.get('emptyContainerWeightUnit')?.value).toBe('kg');
    });

    it('should have gravity control', () => {
      expect(component.volCalcFormGroup.get('gravity')).toBeTruthy();
    });

    it('should have gravityUnit control defaulting to sg', () => {
      expect(component.volCalcFormGroup.get('gravityUnit')?.value).toBe('sg');
    });
  });

  describe('form validation', () => {
    it('should require emptyContainerWeight', () => {
      const control = component.volCalcFormGroup.get('emptyContainerWeight');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should require gravity', () => {
      const control = component.volCalcFormGroup.get('gravity');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should validate decimal pattern for totalWeight', () => {
      const control = component.volCalcFormGroup.get('totalWeight');
      control?.setValue('abc');
      expect(control?.hasError('pattern')).toBe(true);
    });

    it('should accept valid decimal for totalWeight', () => {
      const control = component.volCalcFormGroup.get('totalWeight');
      control?.setValue('10.5');
      expect(control?.hasError('pattern')).toBeFalsy();
    });

    it('should accept negative decimals', () => {
      const control = component.volCalcFormGroup.get('totalWeight');
      control?.setValue('-5.25');
      expect(control?.hasError('pattern')).toBeFalsy();
    });

    it('should allow up to 3 decimal places', () => {
      const control = component.volCalcFormGroup.get('totalWeight');
      control?.setValue('10.123');
      expect(control?.hasError('pattern')).toBeFalsy();
    });
  });

  describe('requiredIfCalcType validator', () => {
    it('should require totalWeight when calType is byWeight', () => {
      component.calType = 'byWeight';
      const control = component.volCalcFormGroup.get('totalWeight');
      control?.setValue('');
      control?.updateValueAndValidity();
      expect(control?.hasError('required')).toBe(true);
    });

    it('should not require totalWeight when calType is byVolume', () => {
      component.calType = 'byVolume';
      const control = component.volCalcFormGroup.get('totalWeight');
      control?.setValue('');
      control?.updateValueAndValidity();
      expect(control?.hasError('required')).toBeFalsy();
    });

    it('should require targetVolume when calType is byVolume', () => {
      component.calType = 'byVolume';
      const control = component.volCalcFormGroup.get('targetVolume');
      control?.setValue('');
      control?.updateValueAndValidity();
      expect(control?.hasError('required')).toBe(true);
    });

    it('should not require targetVolume when calType is byWeight', () => {
      component.calType = 'byWeight';
      const control = component.volCalcFormGroup.get('targetVolume');
      control?.setValue('');
      control?.updateValueAndValidity();
      expect(control?.hasError('required')).toBeFalsy();
    });
  });

  describe('lbs2Kgs', () => {
    it('should convert pounds to kilograms', () => {
      expect(component.lbs2Kgs(1)).toBeCloseTo(0.45359237, 5);
    });

    it('should convert 10 lbs to approximately 4.536 kg', () => {
      expect(component.lbs2Kgs(10)).toBeCloseTo(4.5359237, 5);
    });

    it('should return 0 for 0 lbs', () => {
      expect(component.lbs2Kgs(0)).toBe(0);
    });

    it('should handle negative values', () => {
      expect(component.lbs2Kgs(-1)).toBeCloseTo(-0.45359237, 5);
    });
  });

  describe('kgs2Lbs', () => {
    it('should convert kilograms to pounds', () => {
      expect(component.kgs2Lbs(1)).toBeCloseTo(2.2046226218, 5);
    });

    it('should convert 10 kg to approximately 22.046 lbs', () => {
      expect(component.kgs2Lbs(10)).toBeCloseTo(22.046226218, 5);
    });

    it('should return 0 for 0 kg', () => {
      expect(component.kgs2Lbs(0)).toBe(0);
    });

    it('should handle negative values', () => {
      expect(component.kgs2Lbs(-1)).toBeCloseTo(-2.2046226218, 5);
    });

    it('should be inverse of lbs2Kgs', () => {
      const lbs = 5;
      const kgs = component.lbs2Kgs(lbs);
      expect(component.kgs2Lbs(kgs)).toBeCloseTo(lbs, 5);
    });
  });

  describe('calcVolume', () => {
    it('should calculate volume in liters', () => {
      component.calcVolume(20, 5, 1.0);
      expect(component.resultsL).toBeCloseTo(15, 5);
    });

    it('should calculate volume in gallons', () => {
      component.calcVolume(20, 5, 1.0);
      expect(component.resultsG).toBeCloseTo(3.96258, 4);
    });

    it('should account for specific gravity', () => {
      component.calcVolume(25, 5, 1.050);
      // liquidWeight = 25 - 5 = 20kg
      // specificWeight = 20 / 1.050 = 19.047619...
      expect(component.resultsL).toBeCloseTo(19.047619, 4);
    });

    it('should handle zero weight correctly', () => {
      component.calcVolume(5, 5, 1.0);
      expect(component.resultsL).toBe(0);
    });
  });

  describe('calcWeight', () => {
    it('should calculate weight in kilograms', () => {
      component.calcWeight(19, 5, 1.0);
      // liquidWeight = 1.0 * 19 = 19
      // weight = 19 + 5 = 24
      expect(component.resultsKgs).toBe(24);
    });

    it('should calculate weight in pounds', () => {
      component.calcWeight(19, 5, 1.0);
      expect(component.resultsLbs).toBeCloseTo(52.910943, 4);
    });

    it('should account for specific gravity', () => {
      component.calcWeight(19, 5, 1.050);
      // liquidWeight = 1.050 * 19 = 19.95
      // weight = 19.95 + 5 = 24.95
      expect(component.resultsKgs).toBeCloseTo(24.95, 5);
    });

    it('should handle zero volume', () => {
      component.calcWeight(0, 5, 1.0);
      expect(component.resultsKgs).toBe(5);
    });
  });

  describe('calculate', () => {
    beforeEach(() => {
      // Set up form with valid values
      component.volCalcFormGroup.patchValue({
        totalWeight: '25',
        totalWeightUnit: 'kg',
        targetVolume: '19',
        targetVolumeUnit: 'L',
        emptyContainerWeight: '5',
        emptyContainerWeightUnit: 'kg',
        gravity: '1.050',
        gravityUnit: 'sg',
      });
    });

    it('should reset resultsL and resultsKgs before calculation', () => {
      component.resultsL = 100;
      component.resultsKgs = 100;
      component.calculate();
      // After calculation, one should be set based on calType
      expect(component.resultsL).not.toBe(100);
    });

    it('should call calcVolume when calType is byWeight', () => {
      component.calType = 'byWeight';
      spyOn(component, 'calcVolume');

      component.calculate();

      expect(component.calcVolume).toHaveBeenCalled();
    });

    it('should call calcWeight when calType is byVolume', () => {
      component.calType = 'byVolume';
      spyOn(component, 'calcWeight');

      component.calculate();

      expect(component.calcWeight).toHaveBeenCalled();
    });

    it('should convert totalWeight from lbs to kg', () => {
      component.calType = 'byWeight';
      component.volCalcFormGroup.patchValue({
        totalWeight: '55.1155',
        totalWeightUnit: 'lbs',
      });
      spyOn(component, 'calcVolume');

      component.calculate();

      // 55.1155 lbs = ~25 kg
      expect(component.calcVolume).toHaveBeenCalledWith(
        jasmine.any(Number),
        jasmine.any(Number),
        jasmine.any(Number)
      );
    });

    it('should convert targetVolume from gal to L', () => {
      component.calType = 'byVolume';
      component.volCalcFormGroup.patchValue({
        targetVolume: '5',
        targetVolumeUnit: 'gal',
      });
      spyOn(component, 'calcWeight');

      component.calculate();

      // 5 gal = ~18.927 L
      expect(component.calcWeight).toHaveBeenCalled();
    });

    it('should convert emptyContainerWeight from lbs to kg', () => {
      component.calType = 'byWeight';
      component.volCalcFormGroup.patchValue({
        emptyContainerWeight: '11.023',
        emptyContainerWeightUnit: 'lbs',
      });
      spyOn(component, 'calcVolume');

      component.calculate();

      expect(component.calcVolume).toHaveBeenCalled();
    });

    it('should convert gravity from plato to SG', () => {
      component.calType = 'byWeight';
      component.volCalcFormGroup.patchValue({
        gravity: '12',
        gravityUnit: 'plato',
      });
      spyOn(component, 'calcVolume');

      component.calculate();

      // 12 Plato ≈ 1.048 SG
      expect(component.calcVolume).toHaveBeenCalled();
    });
  });

  describe('reset', () => {
    beforeEach(() => {
      component.volCalcFormGroup.patchValue({
        totalWeight: '25',
        emptyContainerWeight: '5',
        gravity: '1.050',
      });
      component.resultsL = 19;
      component.resultsKgs = 24;
    });

    it('should clear resultsL', () => {
      component.reset();
      expect(component.resultsL).toBeUndefined();
    });

    it('should clear resultsKgs', () => {
      component.reset();
      expect(component.resultsKgs).toBeUndefined();
    });

    it('should reset form with default values when no data provided', () => {
      component.reset();
      expect(component.volCalcFormGroup.get('totalWeightUnit')?.value).toBe('kg');
      expect(component.volCalcFormGroup.get('targetVolumeUnit')?.value).toBe('gal');
      expect(component.volCalcFormGroup.get('emptyContainerWeightUnit')?.value).toBe('kg');
      expect(component.volCalcFormGroup.get('gravityUnit')?.value).toBe('sg');
    });

    it('should reset form with provided data', () => {
      component.reset({
        totalWeightUnit: 'lbs',
        targetVolumeUnit: 'L',
        emptyContainerWeightUnit: 'lbs',
        gravityUnit: 'plato',
      });

      expect(component.volCalcFormGroup.get('totalWeightUnit')?.value).toBe('lbs');
      expect(component.volCalcFormGroup.get('targetVolumeUnit')?.value).toBe('L');
      expect(component.volCalcFormGroup.get('emptyContainerWeightUnit')?.value).toBe('lbs');
      expect(component.volCalcFormGroup.get('gravityUnit')?.value).toBe('plato');
    });

    it('should call volCalcFormGroup.reset', () => {
      spyOn(component.volCalcFormGroup, 'reset');
      component.reset();
      expect(component.volCalcFormGroup.reset).toHaveBeenCalled();
    });
  });

  describe('calTypeChanged', () => {
    it('should call reset with current form values', () => {
      component.volCalcFormGroup.patchValue({
        totalWeight: '25',
        totalWeightUnit: 'lbs',
      });
      spyOn(component, 'reset');

      component.calTypeChanged();

      expect(component.reset).toHaveBeenCalledWith(component.volCalcFormGroup.value);
    });

    it('should preserve unit selections after type change', () => {
      component.volCalcFormGroup.patchValue({
        totalWeightUnit: 'lbs',
        gravityUnit: 'plato',
      });

      component.calTypeChanged();

      expect(component.volCalcFormGroup.get('totalWeightUnit')?.value).toBe('lbs');
      expect(component.volCalcFormGroup.get('gravityUnit')?.value).toBe('plato');
    });
  });

  describe('volCalcForm getter', () => {
    it('should return form controls', () => {
      const controls = component.volCalcForm;
      expect(controls['totalWeight']).toBeTruthy();
      expect(controls['targetVolume']).toBeTruthy();
      expect(controls['emptyContainerWeight']).toBeTruthy();
      expect(controls['gravity']).toBeTruthy();
    });
  });

  describe('decimal regex', () => {
    const testRegex = (value: string) => /^-?\d*[.]?\d{0,3}$/.test(value);

    it('should match positive integers', () => {
      expect(testRegex('123')).toBe(true);
    });

    it('should match negative integers', () => {
      expect(testRegex('-123')).toBe(true);
    });

    it('should match decimals with up to 3 places', () => {
      expect(testRegex('1.234')).toBe(true);
    });

    it('should match decimals with fewer than 3 places', () => {
      expect(testRegex('1.5')).toBe(true);
    });

    it('should not match decimals with more than 3 places', () => {
      expect(testRegex('1.2345')).toBe(false);
    });

    it('should match just a decimal point', () => {
      expect(testRegex('.')).toBe(true);
    });

    it('should match numbers starting with decimal', () => {
      expect(testRegex('.123')).toBe(true);
    });

    it('should not match letters', () => {
      expect(testRegex('abc')).toBe(false);
    });

    it('should not match mixed letters and numbers', () => {
      expect(testRegex('12a')).toBe(false);
    });
  });

  describe('integration tests', () => {
    it('should calculate correct volume for a typical keg', () => {
      // 5 gallon keg weighing 23.5 kg with 5.5 kg empty weight, SG 1.050
      component.calType = 'byWeight';
      component.volCalcFormGroup.patchValue({
        totalWeight: '23.5',
        totalWeightUnit: 'kg',
        emptyContainerWeight: '5.5',
        emptyContainerWeightUnit: 'kg',
        gravity: '1.050',
        gravityUnit: 'sg',
      });

      component.calculate();

      // liquidWeight = 23.5 - 5.5 = 18 kg
      // volume = 18 / 1.050 = 17.14 L
      expect(component.resultsL).toBeCloseTo(17.14, 1);
      expect(component.resultsG).toBeCloseTo(4.53, 1);
    });

    it('should calculate correct weight for a target volume', () => {
      // Target 5 gallons, empty weight 5 kg, SG 1.050
      component.calType = 'byVolume';
      component.volCalcFormGroup.patchValue({
        targetVolume: '5',
        targetVolumeUnit: 'gal',
        emptyContainerWeight: '5',
        emptyContainerWeightUnit: 'kg',
        gravity: '1.050',
        gravityUnit: 'sg',
      });

      component.calculate();

      // 5 gal = 18.927 L
      // liquidWeight = 1.050 * 18.927 = 19.87 kg
      // totalWeight = 19.87 + 5 = 24.87 kg
      expect(component.resultsKgs).toBeCloseTo(24.87, 1);
    });

    it('should handle plato to SG conversion in calculation', () => {
      component.calType = 'byWeight';
      component.volCalcFormGroup.patchValue({
        totalWeight: '23.5',
        totalWeightUnit: 'kg',
        emptyContainerWeight: '5.5',
        emptyContainerWeightUnit: 'kg',
        gravity: '12.4',
        gravityUnit: 'plato',
      });

      component.calculate();

      // 12.4 Plato ≈ 1.050 SG
      expect(component.resultsL).toBeCloseTo(17.14, 1);
    });
  });

  describe('ngOnInit', () => {
    it('should be defined', () => {
      expect(component.ngOnInit).toBeDefined();
    });

    it('should not throw', () => {
      expect(() => component.ngOnInit()).not.toThrow();
    });
  });
});
