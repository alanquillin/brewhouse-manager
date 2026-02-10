import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { Component, Inject } from '@angular/core';

@Component({
  selector: 'app-image-preview-dialog',
  templateUrl: 'image-preview-dialog.component.html',
  styleUrls: ['image-preview-dialog.component.scss'],
  standalone: false,
})
export class LocationImageDialogComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<LocationImageDialogComponent>
  ) {}

  onClick(): void {
    this.dialogRef.close();
  }
}
