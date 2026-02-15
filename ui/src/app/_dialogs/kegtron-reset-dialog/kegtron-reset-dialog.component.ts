import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DataError, DataService } from '../../_services/data.service';

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

  volumeUnits = [
    { value: 'gal', label: 'Gallons' },
    { value: 'l', label: 'Liters' },
    { value: 'ml', label: 'Milliliters' },
  ];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: { deviceId: string; portNum: number },
    public dialogRef: MatDialogRef<KegtronResetDialogComponent>,
    private dataService: DataService,
    private _snackBar: MatSnackBar
  ) {}

  submit(): void {
    this.processing = true;
    this.dataService
      .resetKegtronPort(this.data.deviceId, this.data.portNum, {
        volumeSize: this.volumeSize,
        volumeUnit: this.volumeUnit,
      })
      .subscribe({
        next: () => {
          this.processing = false;
          this.dialogRef.close('submit');
        },
        error: (err: DataError) => {
          this._snackBar.open('Error: ' + err.message, 'Close');
          this.processing = false;
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
