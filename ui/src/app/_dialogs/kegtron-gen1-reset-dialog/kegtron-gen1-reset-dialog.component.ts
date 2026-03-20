import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DataError, DataService } from '../../_services/data.service';
import { isNilOrEmpty } from '../../utils/helpers';

@Component({
  selector: 'app-kegtron-gen1-reset-dialog',
  templateUrl: './kegtron-gen1-reset-dialog.component.html',
  styleUrls: ['./kegtron-gen1-reset-dialog.component.scss'],
  standalone: false,
})
export class KegtronGen1ResetDialogComponent {
  kegSize: number | null = null;
  startVolume: number | null = null;
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
      portIndex: number;
      showSkip?: boolean;
    },
    public dialogRef: MatDialogRef<KegtronGen1ResetDialogComponent>,
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
      kegSize: this.kegSize,
      startVolume: this.startVolume,
      volumeUnit: this.volumeUnit,
    };

    this.dataService
      .resetKegtronGen1Port(this.data.deviceId, this.data.portIndex, payload)
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
