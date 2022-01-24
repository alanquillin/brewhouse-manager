// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */

import { Injectable } from '@angular/core';
import { Observable, throwError, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../environments/environment';
import { Location, Tap, Beer, Sensor, DataError, UserInfo } from './models/models';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import * as _ from 'lodash';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' })
};

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

    this.host = 'https://localhost:5000';
    this.baseUrl = this.host + '/api/v1';
  }

  getError(error: any){
    console.log("error caught")
    let errObj = new DataError(error.error.message);
    if (!(error.error instanceof ErrorEvent)) {
        // handle server-side errors
        errObj.reason = error.message;
        errObj.statusCode = error.status;
        errObj.statusText = error.statusText;
    }
    return throwError(() => errObj);
  }

  login(email: string, password: string): Observable<any>{
    const url = `${this.host}/login`;
    return this.http.post<any>(url, {email, password}, httpOptions).pipe(catchError(this.getError));
  }

  getLocations(): Observable<Location[]> {
    const url = `${this.baseUrl}/locations`;
    return this.http.get<Location[]>(url).pipe(catchError(this.getError));
  }

  getLocation(location: any): Observable<Location> {
    const url = `${this.baseUrl}/locations/${location}`;
    return this.http.get<Location>(url).pipe(catchError(this.getError));
  }

  createLocation(data: any): Observable<Location> {
    const url = `${this.baseUrl}/locations`;
    return this.http.post<Location>(url, data).pipe(catchError(this.getError));
  }

  deleteLocation(location: string): Observable<any> {
    const url = `${this.baseUrl}/locations/${location}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  updateLocation(location: string, data: any): Observable<Location> {
    const url = `${this.baseUrl}/locations/${location}`;
    return this.http.patch<Location>(url, data).pipe(catchError(this.getError));
  }

  getTaps(locationId?: string): Observable<Tap[]> {
    var url: string;
    if(_.isNil(locationId)) {
      url = `${this.baseUrl}/taps`;
    } else {
      url = `${this.baseUrl}/locations/${locationId}/taps`;
    }

    return this.http.get<Tap[]>(url).pipe(catchError(this.getError));
  }

  getTap(tapId: string): Observable<Tap> {
    const url = `${this.baseUrl}/taps/${tapId}`;
    return this.http.get<Tap>(url).pipe(catchError(this.getError));
  }

  createTap(data: any): Observable<Tap> {
    const url = `${this.baseUrl}/taps`;
    return this.http.post<Tap>(url, data).pipe(catchError(this.getError));
  }

  updateTap(tapId: string, data: any): Observable<Tap> {
    const url = `${this.baseUrl}/taps/${tapId}`;
    return this.http.patch<Tap>(url, data).pipe(catchError(this.getError));
  }

  deleteTap(tapId: string): Observable<any> {
    const url = `${this.baseUrl}/taps/${tapId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  getBeers(): Observable<Beer[]> {
    const url = `${this.baseUrl}/beers`;
    return this.http.get<Beer[]>(url).pipe(catchError(this.getError));
  }

  createBeer(data: any): Observable<Beer[]> {
    const url = `${this.baseUrl}/beers`;
    return this.http.post<Beer[]>(url, data).pipe(catchError(this.getError));
  }

  getBeer(beerId: string): Observable<Beer> {
    const url = `${this.baseUrl}/beers/${beerId}`;
    return this.http.get<Beer>(url).pipe(catchError(this.getError));
  }

  deleteBeer(beerId: string): Observable<any> {
    const url = `${this.baseUrl}/beers/${beerId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  updateBeer(beerId: string, data: any): Observable<Beer> {
    const url = `${this.baseUrl}/beers/${beerId}`;
    return this.http.patch<Beer>(url, data).pipe(catchError(this.getError));
  }

  getSensors(locationId?: string): Observable<Sensor[]> {
    var url: string;
    if (_.isNil(locationId)) {
      url = `${this.baseUrl}/sensors`;
    } else {
      url = `${this.baseUrl}/locations/${locationId}/sensors`;
    }

    return this.http.get<Sensor[]>(url).pipe(catchError(this.getError));
  }

  getSensor(sensorId: string): Observable<Sensor> {
    const url = `${this.baseUrl}/sensors/${sensorId}`;
    return this.http.get<Sensor>(url).pipe(catchError(this.getError));
  }

  createSensor(data: any): Observable<Sensor> {
    const url = `${this.baseUrl}/sensors`;
    return this.http.post<Sensor>(url, data).pipe(catchError(this.getError));
  }

  updateSensor(sensorId: string, data: any): Observable<Sensor> {
    const url = `${this.baseUrl}/sensors/${sensorId}`;
    return this.http.patch<Sensor>(url, data).pipe(catchError(this.getError));
  }

  deleteSensor(sensorId: string): Observable<any> {
    const url = `${this.baseUrl}/sensors/${sensorId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  getSensorType(): Observable<string[]> {
    const url = `${this.baseUrl}/sensors/types`;
    return this.http.get<string[]>(url).pipe(catchError(this.getError));
  }

  getSensorData(sensorId: string, dataType: string): Observable<any> {
    const url = `${this.baseUrl}/sensors/${sensorId}/${dataType}`;
    return this.http.get<any>(url).pipe(catchError(this.getError));
  }

  getPercentBeerRemaining(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "percent_beer_remaining");
  }

  getCurrentUser(): Observable<UserInfo> {
    const url = `${this.baseUrl}/admins/current`;
    return this.http.get<UserInfo>(url).pipe(catchError(this.getError));
  }

  updateAdmin(adminId: string, data: object): Observable<UserInfo> {
    const url = `${this.baseUrl}/admins/${adminId}`;
    return this.http.patch<UserInfo>(url, data).pipe(catchError(this.getError));
  }
}
