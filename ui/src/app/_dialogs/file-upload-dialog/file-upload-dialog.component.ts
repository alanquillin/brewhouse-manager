import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { ExtendedFile } from '../../_components/file-uploader/file-uploader.component';
import { toBoolean } from '../../utils/helpers';

import * as _ from 'lodash';

@Component({
  selector: 'app-file-upload-dialog',
  templateUrl: './file-upload-dialog.component.html',
  styleUrls: ['./file-upload-dialog.component.scss'],
  standalone: false,
})
export class FileUploadDialogComponent {
  data = inject(MAT_DIALOG_DATA);
  dialogRef = inject<MatDialogRef<FileUploadDialogComponent>>(MatDialogRef);

  imageType: string;
  allowMultiple: boolean;
  closeOnComplete: boolean;

  constructor() {
    const data = this.data;

    this.imageType = data.imageType;
    this.allowMultiple = toBoolean(_.get(data, 'allowMultiple', false));
    this.closeOnComplete = toBoolean(_.get(data, 'closeOnComplete', true));
  }

  onUploadComplete(file: ExtendedFile) {}

  onAllUploadsComplete(files: ExtendedFile[]) {
    if (this.closeOnComplete) {
      this.dialogRef.close(files);
    }
  }
}
