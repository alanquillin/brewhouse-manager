import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageSensorsComponent } from './sensors.component';

describe('SensorsComponent', () => {
  let component: ManageSensorsComponent;
  let fixture: ComponentFixture<ManageSensorsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ManageSensorsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageSensorsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
