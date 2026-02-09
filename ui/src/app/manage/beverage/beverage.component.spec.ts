import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageBeverageComponent } from './beverage.component';

describe('ManageBeverageComponent', () => {
  let component: ManageBeverageComponent;
  let fixture: ComponentFixture<ManageBeverageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ManageBeverageComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageBeverageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
