import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { isNilOrEmpty } from 'src/app/utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-qrcode-dialog',
  templateUrl: 'qrcode-dialog.component.html',
  styleUrls: ['qrcode-dialog.component.scss'],
  standalone: false,
})
export class LocationQRCodeDialogComponent {
  data = inject(MAT_DIALOG_DATA);
  dialogRef = inject<MatDialogRef<LocationQRCodeDialogComponent>>(MatDialogRef);

  url: string;
  title: string;
  width: number;

  isNilOrEmpty = isNilOrEmpty;
  _ = _;

  constructor() {
    const data = this.data;

    this.url = data.url;
    this.title = _.get(data, 'title', '');
    this.width = _.toInteger(_.get(data, 'width', 600));
  }

  onClick(): void {
    this.dialogRef.close();
  }
}
