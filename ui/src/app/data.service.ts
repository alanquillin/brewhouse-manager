// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */

import { Injectable, Inject } from '@angular/core';
import { Observable, throwError, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Location, Tap, Beer, Sensor, DataError, UserInfo, Settings } from './models/models';
import { WINDOW } from './window.provider';

import * as _ from 'lodash';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' })
};

@Injectable({
  providedIn: 'root',
})
export class DataService {
  apiBaseUrl: string;
  baseUrl: string;

  constructor(public http: HttpClient, @Inject(WINDOW) private window: Window) {
    console.log(this.window.location)
    const protocol = this.window.location.protocol
    const hostname = this.window.location.hostname;
    const port = this.window.location.port
    this.baseUrl = `${protocol}//${hostname}`;

    if (!((protocol === 'http:' && port === "80") || (protocol === 'https:' && port === "443"))){
      this.baseUrl = `${this.baseUrl}:${port}`;
    }

    this.apiBaseUrl = this.baseUrl + '/api/v1';
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
    const url = `${this.baseUrl}/login`;
    return this.http.post<any>(url, {email, password}, httpOptions).pipe(catchError(this.getError));
  }

  getLocations(): Observable<Location[]> {
    const url = `${this.apiBaseUrl}/locations`;
    return this.http.get<Location[]>(url).pipe(catchError(this.getError));
  }

  getLocation(location: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.get<Location>(url).pipe(catchError(this.getError));
  }

  createLocation(data: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations`;
    return this.http.post<Location>(url, data).pipe(catchError(this.getError));
  }

  deleteLocation(location: string): Observable<any> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  updateLocation(location: string, data: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.patch<Location>(url, data).pipe(catchError(this.getError));
  }

  getTaps(locationId?: string): Observable<Tap[]> {
    var url: string;
    if(_.isNil(locationId)) {
      url = `${this.apiBaseUrl}/taps`;
    } else {
      url = `${this.apiBaseUrl}/locations/${locationId}/taps`;
    }

    return this.http.get<Tap[]>(url).pipe(catchError(this.getError));
  }

  getTap(tapId: string): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.get<Tap>(url).pipe(catchError(this.getError));
  }

  createTap(data: any): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps`;
    return this.http.post<Tap>(url, data).pipe(catchError(this.getError));
  }

  updateTap(tapId: string, data: any): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.patch<Tap>(url, data).pipe(catchError(this.getError));
  }

  deleteTap(tapId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  getBeers(): Observable<Beer[]> {
    const url = `${this.apiBaseUrl}/beers`;
    return this.http.get<Beer[]>(url).pipe(catchError(this.getError));
  }

  createBeer(data: any): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers`;
    return this.http.post<Beer>(url, data).pipe(catchError(this.getError));
  }

  getBeer(beerId: string): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.get<Beer>(url).pipe(catchError(this.getError));
  }

  deleteBeer(beerId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  updateBeer(beerId: string, data: any): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.patch<Beer>(url, data).pipe(catchError(this.getError));
  }

  getSensors(locationId?: string): Observable<Sensor[]> {
    var url: string;
    if (_.isNil(locationId)) {
      url = `${this.apiBaseUrl}/sensors`;
    } else {
      url = `${this.apiBaseUrl}/locations/${locationId}/sensors`;
    }

    return this.http.get<Sensor[]>(url).pipe(catchError(this.getError));
  }

  getSensor(sensorId: string): Observable<Sensor> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}`;
    return this.http.get<Sensor>(url).pipe(catchError(this.getError));
  }

  createSensor(data: any): Observable<Sensor> {
    const url = `${this.apiBaseUrl}/sensors`;
    return this.http.post<Sensor>(url, data).pipe(catchError(this.getError));
  }

  updateSensor(sensorId: string, data: any): Observable<Sensor> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}`;
    return this.http.patch<Sensor>(url, data).pipe(catchError(this.getError));
  }

  deleteSensor(sensorId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  getSensorType(): Observable<string[]> {
    const url = `${this.apiBaseUrl}/sensors/types`;
    return this.http.get<string[]>(url).pipe(catchError(this.getError));
  }

  getSensorData(sensorId: string, dataType: string): Observable<any> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}/${dataType}`;
    return this.http.get<any>(url).pipe(catchError(this.getError));
  }

  getPercentBeerRemaining(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "percent_beer_remaining");
  }

  getCurrentUser(): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/current`;
    return this.http.get<UserInfo>(url).pipe(catchError(this.getError));
  }

  getUsers(): Observable<UserInfo[]> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.get<UserInfo[]>(url).pipe(catchError(this.getError));
  }

  getUser(userId: string): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.get<UserInfo>(url).pipe(catchError(this.getError));
  }

  createUser(data: any): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.post<UserInfo>(url, data).pipe(catchError(this.getError));
  }

  updateUser(userId: string, data: object): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.patch<UserInfo>(url, data).pipe(catchError(this.getError));
  }

  deleteUser(userId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.delete<any>(url).pipe(catchError(this.getError));
  }

  getSettings(): Observable<Settings> {
    const url = `${this.apiBaseUrl}/settings`;
    return this.http.get<Settings>(url).pipe(catchError(this.getError));
  }

  uploadImage(imageType: string, file: File): Observable<any> {
    const url = `${this.apiBaseUrl}/uploads/images/${imageType}`;
    const formData: FormData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(url, formData, {reportProgress: true}).pipe(catchError(this.getError));
  }

  uploadBeerImage(file: File): Observable<any> {
    return this.uploadImage('beer', file);
  }

  uploadUserImage(file: File): Observable<any> {
    return this.uploadImage('user', file);
  }
}
