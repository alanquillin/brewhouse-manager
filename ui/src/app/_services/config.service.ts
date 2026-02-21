import { EventEmitter, Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class ConfigService {
  updated = new EventEmitter<any>();

  constructor() {}

  update(data: any): void {
    this.updated.emit(data);
  }
}
