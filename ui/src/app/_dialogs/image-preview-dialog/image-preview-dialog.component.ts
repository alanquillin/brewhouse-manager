import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { Component, inject } from '@angular/core';

@Component({
  selector: 'app-image-preview-dialog',
  templateUrl: 'image-preview-dialog.component.html',
  styleUrls: ['image-preview-dialog.component.scss'],
  standalone: false,
})
export class LocationImageDialogComponent {
  data = inject(MAT_DIALOG_DATA);
  dialogRef = inject<MatDialogRef<LocationImageDialogComponent>>(MatDialogRef);

  onClick(): void {
    this.dialogRef.close();
  }
}
