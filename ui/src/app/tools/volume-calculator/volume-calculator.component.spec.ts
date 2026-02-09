import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VolumeCalculatorComponent } from './volume-calculator.component';

describe('VolumeCalculatorComponent', () => {
  let component: VolumeCalculatorComponent;
  let fixture: ComponentFixture<VolumeCalculatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VolumeCalculatorComponent],
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
});
