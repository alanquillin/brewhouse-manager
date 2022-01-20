import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageHeaderComponent } from './header.component';

describe('HeaderComponent', () => {
  let component: ManageHeaderComponent;
  let fixture: ComponentFixture<ManageHeaderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ManageHeaderComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageHeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
