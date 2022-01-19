import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageLocationsComponent } from './locations.component';

describe('LocationsComponent', () => {
  let component: ManageLocationsComponent;
  let fixture: ComponentFixture<ManageLocationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ManageLocationsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageLocationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
