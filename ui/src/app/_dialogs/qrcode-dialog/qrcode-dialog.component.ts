import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { isNilOrEmpty } from 'src/app/utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'qrcode-dialog',
  templateUrl: 'qrcode-dialog.component.html',
  styleUrls: ['qrcode-dialog.component.scss'],
  standalone: false,
})
export class LocationQRCodeDialog {
  url: string;
  title: string;
  width: number;

  isNilOrEmpty: Function = isNilOrEmpty;
  _ = _;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<LocationQRCodeDialog>
  ) {
    this.url = data.url;
    this.title = _.get(data, 'title', '');
    this.width = _.toInteger(_.get(data, 'width', 600));
  }

  onClick(): void {
    this.dialogRef.close();
  }
}
