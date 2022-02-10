import { Component, ViewChild, ElementRef, Input, AfterViewInit, Output, EventEmitter } from "@angular/core";
import { DataService, DataError } from '../../_services/data.service';
import { MatSnackBar } from '@angular/material/snack-bar';

import { HttpEventType } from "@angular/common/http";

import * as _ from 'lodash';
import * as $ from 'jquery';

export class ExtendedFile extends File {
  progress: number = 0;
  path:string | undefined;
  hasError: boolean = false
  errorMessage: string | undefined
}

@Component({
  selector: 'app-file-uploader',
  templateUrl: './file-uploader.component.html',
  styleUrls: ['./file-uploader.component.scss']
})
export class FileUploaderComponent implements AfterViewInit{
  @Input() imageType: string = "";
  @Input() allowMultiple: boolean = false;

  @Output() uploadComplete = new EventEmitter<ExtendedFile>();
  @Output() uploadsComplete = new EventEmitter<ExtendedFile[]>();

  @ViewChild("fileDropRef", { static: false }) fileDropEl: ElementRef | undefined;
  
  uploading = false;
  files: any = {};

  _ = _;

  constructor(private dataService: DataService, private _snackBar: MatSnackBar) { }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  /**
   * on file drop handler
   */
  onFileDropped(files: File[]): void {
    if(this.uploading){
      return;
    }

    if(!this.allowMultiple && files.length > 1){
      this.displayError("Mutli-file uploads are disabled.")
      return;
    }

    this.uploadFiles(files);
  }

  /**
   * handle file from browsing
   */
  fileBrowseHandler($event: any): void {
    if(this.uploading){
      return;
    }

    if(_.isNil($event)){
      return;
    }
    var files = $event.target.files;
    this.uploadFiles(files);
  }

  areUploadsComplete(includeFailures:boolean = false): boolean {
    const _files = _.values(this.files)
    for(const _f of _files){
      if(_f.progress < 100 ) {
        if(includeFailures && _f.hasError)
          continue;
        return false;
      }
    }
    return true;
  }

  upload(file: ExtendedFile) {
    this.dataService.uploadImage(this.imageType, file).subscribe({
      next: (event: any) => {
        if (event.type === HttpEventType.UploadProgress) {
          file.progress = Math.round(100 * event.loaded / event.total);
        } else {
          file.progress = 100;
          file.path = event.destinationPath;
          this.uploadComplete.emit(file);
          if(this.allowMultiple) {
            if(this.areUploadsComplete()) {
              this.uploadsComplete.emit(_.values(this.files));
              this.uploading = false;
            }
          } else {
            this.uploadsComplete.emit([file]);
          }
        }
      },
      error: (err: DataError) => {
        file.progress = 0;
        file.hasError = true;
        file.errorMessage = err.message
        if(this.allowMultiple) {
          if(this.areUploadsComplete(true)) {
            this.uploading = false;
          }
        } else {
          this.uploading = false;
        }
      }
    })
  }

  uploadFiles(files: File[]) {
    this.uploading = true;
    this.files = {}
    for (const _file of files) {
      const file = <ExtendedFile>_file;
      if(_.get(this.files, file.name)){
        continue;
      }
      file.progress = 0;
      file.hasError = false;
      this.files[file.name] = file;
      this.upload(file);
    }

    if(!_.isNil(this.fileDropEl)){
      this.fileDropEl.nativeElement.value = "";
    }
  }

  /**
   * format bytes
   * @param bytes (File size in bytes)
   * @param decimals (Decimals point)
   */
  formatBytes(bytes: number, decimals = 2) {
    if (bytes === 0) {
      return "0 Bytes";
    }
    const k = 1024;
    const dm = decimals <= 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  }

  ngAfterViewInit() {
    if(this.allowMultiple) {
      $( "#fileDropRef" ).attr("multiple", "true")
    }
  }
}
