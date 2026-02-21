import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DataError, DataService } from '../../_services/data.service';
import { isNilOrEmpty } from '../../utils/helpers';

@Component({
  selector: 'app-kegtron-reset-dialog',
  templateUrl: './kegtron-reset-dialog.component.html',
  styleUrls: ['./kegtron-reset-dialog.component.scss'],
  standalone: false,
})
export class KegtronResetDialogComponent {
  volumeSize: number | null = null;
  volumeUnit = 'gal';
  processing = false;
  showSkip = false;
  isNilOrEmpty = isNilOrEmpty;

  volumeUnits = [
    { value: 'gal', label: 'Gallons' },
    { value: 'l', label: 'Liters' },
    { value: 'ml', label: 'Milliliters' },
  ];

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: {
      deviceId: string;
      portNum: number;
      showSkip?: boolean;
      updateDateTapped?: boolean;
      batchId?: string;
    },
    public dialogRef: MatDialogRef<KegtronResetDialogComponent>,
    private dataService: DataService,
    private _snackBar: MatSnackBar
  ) {
    this.showSkip = data.showSkip ?? false;
    this.dialogRef.disableClose = false;
  }

  submit(): void {
    this.processing = true;
    this.dialogRef.disableClose = true;
    const payload: any = {
      volumeSize: this.volumeSize,
      volumeUnit: this.volumeUnit,
    };
    if (this.data.batchId) {
      payload.batchId = this.data.batchId;
    }

    this.dataService
      .resetKegtronPort(this.data.deviceId, this.data.portNum, payload, this.data.updateDateTapped)
      .subscribe({
        next: () => {
          this.processing = false;
          this.dialogRef.disableClose = false;
          this.dialogRef.close('submit');
        },
        error: (err: DataError) => {
          this._snackBar.open('Error: ' + err.message, 'Close');
          this.processing = false;
          this.dialogRef.disableClose = false;
        },
      });
  }

  skip(): void {
    this.dialogRef.close('skip');
  }

  cancel(): void {
    this.dialogRef.close('cancel');
  }
}
