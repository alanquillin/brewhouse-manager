import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageBeerComponent } from './beer.component';

describe('BeerComponent', () => {
  let component: ManageBeerComponent;
  let fixture: ComponentFixture<ManageBeerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ManageBeerComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageBeerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
