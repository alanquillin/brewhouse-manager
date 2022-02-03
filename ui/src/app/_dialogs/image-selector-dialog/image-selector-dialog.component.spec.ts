import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageSelectorDialogComponent } from './image-selector-dialog.component';

describe('ImageSelectorDialogComponent', () => {
  let component: ImageSelectorDialogComponent;
  let fixture: ComponentFixture<ImageSelectorDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ImageSelectorDialogComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ImageSelectorDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
