import { MAT_DIALOG_DATA } from '@angular/material/dialog';

import { Component, Inject } from '@angular/core';

@Component({
  selector: 'qrcode-dialog',
  templateUrl: 'qrcode-dialog.component.html',
  styleUrls: ['qrcode-dialog.component.scss']
})

export class LocationQRCodeDialog {
  url: string;
  constructor(@Inject(MAT_DIALOG_DATA) public data: any) {
    this.url = data.url;
  }
}
