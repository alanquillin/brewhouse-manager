import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageTapsComponent } from './taps.component';

describe('TapsComponent', () => {
  let component: ManageTapsComponent;
  let fixture: ComponentFixture<ManageTapsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ManageTapsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageTapsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
