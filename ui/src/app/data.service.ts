// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */

import { Injectable } from '@angular/core';
import { Observable, throwError, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../environments/environment';
import { Location, Tap, Beer, Sensor } from './models/models';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class DataService {
  baseUrl: string;
  host: string;

  constructor(public http: HttpClient) {
    // if (!environment.production) {
    //   const schema = environment.apiSchema;
    //   const host = environment.apiHost;
    //   const port = environment.apiPort;
    //   this.host = `${schema}://${host}:${port}`;
    //   this.baseUrl = `${this.host}`;
    // } else {
    //   this.host = '';
    //   this.baseUrl = '/api/v1';
    // }

    this.host = '';
    this.baseUrl = '/api/v1';
  }

  getError(error: any) {
    let message = '';
    if (error.error instanceof ErrorEvent) {
        // handle client-side errors
        message = `Error: ${error.error.message}`;
    } else {
        // handle server-side errors
        message = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    console.log(message);
    return throwError(message);
  }

  getLocations(): Observable<Location[]> {
    const url = `${this.baseUrl}/locations`;
    return this.http.get<Location[]>(url).pipe(catchError(this.getError));
  }

  getLocation(location: any): Observable<Location> {
    const url = `${this.baseUrl}/locations/${location}`;
    return this.http.get<Location>(url).pipe(catchError(this.getError));
  }

  getTaps(locationId: string): Observable<Tap[]> {
    const url = `${this.baseUrl}/locations/${locationId}/taps`;
    return this.http.get<Tap[]>(url).pipe(catchError(this.getError));
  }

  getTap(tapId: string, locationId: string): Observable<Tap> {
    const url = `${this.baseUrl}/locations/${locationId}/taps/${tapId}`;
    return this.http.get<Tap>(url).pipe(catchError(this.getError));
  }

  getBeer(beerId: string, locationId: string): Observable<Beer> {
    const url = `${this.baseUrl}/locations/${locationId}/beers/${beerId}`;
    return this.http.get<Beer>(url).pipe(catchError(this.getError));
  }

  getSensor(sensorId: string, locationId: string): Observable<Sensor> {
    const url = `${this.baseUrl}/locations/${locationId}/sensors/${sensorId}`;
    return this.http.get<Sensor>(url).pipe(catchError(this.getError));
  }

  getSensorData(sensorId: string, locationId: string, dataType: string): Observable<any> {
    const url = `${this.baseUrl}/locations/${locationId}/sensors/${sensorId}/${dataType}`;
    return this.http.get<any>(url).pipe(catchError(this.getError));
  }

  getPercentBeerRemaining(sensorId: string, locationId: string): Observable<number> {
    return this.getSensorData(sensorId, locationId, "percent_beer_remaining");
  }
}
