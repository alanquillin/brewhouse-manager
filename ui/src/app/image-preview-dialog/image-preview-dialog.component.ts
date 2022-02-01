import { MAT_DIALOG_DATA } from '@angular/material/dialog';

import { Component, Inject } from '@angular/core';

@Component({
  selector: 'image-preview-dialog',
  templateUrl: 'image-preview-dialog.component.html',
  styleUrls: ['image-preview-dialog.component.scss']
})
export class LocationImageDialog {
  constructor(@Inject(MAT_DIALOG_DATA) public data: any) {}
}
