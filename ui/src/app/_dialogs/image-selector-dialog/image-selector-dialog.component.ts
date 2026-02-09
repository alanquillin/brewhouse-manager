import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DataError, DataService } from '../../_services/data.service';

import { isNilOrEmpty } from '../../utils/helpers';

@Component({
  selector: 'app-image-selector-dialog',
  templateUrl: './image-selector-dialog.component.html',
  styleUrls: ['./image-selector-dialog.component.scss'],
  standalone: false,
})
export class ImageSelectorDialogComponent implements OnInit {
  selectedImage: string | undefined;
  currentImage: string;
  imageType: string;
  images: string[] = [];
  processing = false;

  isNilOrEmpty: Function = isNilOrEmpty;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ImageSelectorDialogComponent>,
    private dataService: DataService,
    private _snackBar: MatSnackBar
  ) {
    this.currentImage = data.currentImage;
    this.imageType = data.imageType;
    this.processing = false;
  }

  displayError(errMsg: string) {
    this._snackBar.open('Error: ' + errMsg, 'Close');
  }

  ngOnInit(): void {
    this.processing = true;
    this.dataService.listImages(this.imageType).subscribe({
      next: (images: string[]) => {
        this.images = images;
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      },
    });
  }

  closeWithSelectedImage(): void {
    this.dialogRef.close(this.selectedImage);
  }

  onClick(image: string): void {
    this.selectedImage = image;
  }

  onDoubleClick(image: string): void {
    this.selectedImage = image;
    this.closeWithSelectedImage();
  }

  select() {
    this.closeWithSelectedImage();
  }
}
