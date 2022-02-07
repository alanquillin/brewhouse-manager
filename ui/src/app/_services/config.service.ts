import { Injectable, EventEmitter } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  updated = new EventEmitter<any>();
  
  constructor() { }

  update(data: any): void {
    this.updated.emit(data)
  }
}
