import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Component, Inject, OnInit } from '@angular/core';
import { DataService, DataError } from '../../_services/data.service';
import { MatSnackBar } from '@angular/material/snack-bar';

import * as _ from 'lodash';
import { isNilOrEmpty } from '../../utils/helpers';



@Component({
  selector: 'app-image-selector-dialog',
  templateUrl: './image-selector-dialog.component.html',
  styleUrls: ['./image-selector-dialog.component.scss']
})
export class ImageSelectorDialogComponent implements OnInit {

  selectedImage: string | undefined;
  currentImage: string
  imageType: string;
  images: string[] = []

  isNilOrEmpty: Function = isNilOrEmpty;

  constructor(@Inject(MAT_DIALOG_DATA) public data: any, public dialogRef: MatDialogRef<ImageSelectorDialogComponent>, private dataService: DataService, private _snackBar: MatSnackBar) {
    this.currentImage = data.currentImage;
    this.imageType = data.imageType;
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  ngOnInit(): void {
    this.dataService.listImages(this.imageType).subscribe({
      next: (images: string[]) => {
        this.images = images;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
      }
    })
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

  select(){
    this.closeWithSelectedImage();
  }
}
