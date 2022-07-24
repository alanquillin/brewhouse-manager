// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */

import { Injectable, Inject, EventEmitter, Output } from '@angular/core';
import { Observable, throwError, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Location, Tap, Beer, Beverage, Sensor, UserInfo, Settings } from '../models/models';
import { WINDOW } from '../window.provider';
import { isNilOrEmpty } from '../utils/helpers';

import * as _ from 'lodash';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' })
};

export class DataError extends Error {
  statusCode!: number;
  statusText!: string;
  reason!: string;

  constructor(message?: string, statusCode?: any | undefined, statusText?: any | undefined, reason?: any | undefined){
    super(message);
    if (statusCode !== undefined){
      this.statusCode = statusCode;
    }
    if (statusText !== undefined) {
      this.statusText = statusText
    }
    if (reason !== undefined) {
      this.reason = reason;
    }
  }
}

@Injectable({
  providedIn: 'root',
})
export class DataService {
  unauthorized: EventEmitter<DataError> 

  apiBaseUrl: string;
  baseUrl: string;

  constructor(public http: HttpClient, @Inject(WINDOW) private window: Window) {
    this.unauthorized = new EventEmitter();

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
    let errObj = new DataError(error.error.message);
    if (!(error.error instanceof ErrorEvent)) {
      // handle server-side errors
      errObj.reason = error.message;
      errObj.statusCode = _.toInteger(error.status);
      errObj.statusText = error.statusText;

      if(errObj.statusCode === 401) {
        this.unauthorized.emit(errObj);
      }

      // This is a work around in case the browser got a 302 to redirect to the login page, but the original
      // request was not a GET so it tried to make an invalid request to /login instead of redirecting to the page
      if(errObj.statusCode === 405 && (!isNilOrEmpty(error.url) && _.startsWith(error.url, `${this.baseUrl}/login`))){
        window.location.href = error.url;
      }
    }
    return throwError(() => {return errObj});
  }

  login(email: string, password: string): Observable<any>{
    const url = `${this.baseUrl}/login`;
    return this.http.post<any>(url, {email, password}, httpOptions).pipe(catchError((err: any) => this.getError(err)));
  }

  getLocations(): Observable<Location[]> {
    const url = `${this.apiBaseUrl}/locations`;
    return this.http.get<Location[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getLocation(location: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.get<Location>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createLocation(data: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations`;
    return this.http.post<Location>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteLocation(location: string): Observable<any> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.delete<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateLocation(location: string, data: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.patch<Location>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  getTaps(locationId?: string): Observable<Tap[]> {
    var url: string;
    if(_.isNil(locationId)) {
      url = `${this.apiBaseUrl}/taps`;
    } else {
      url = `${this.apiBaseUrl}/locations/${locationId}/taps`;
    }

    return this.http.get<Tap[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getTap(tapId: string): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.get<Tap>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createTap(data: any): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps`;
    return this.http.post<Tap>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateTap(tapId: string, data: any): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.patch<Tap>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteTap(tapId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.delete<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  clearBeerFromTap(tapId: string): Observable<any> {
    return this.updateTap(tapId, {"beerId": null});
  }

  clearBeverageFromTap(tapId: string): Observable<any> {
    return this.updateTap(tapId, {"beverageId": null});
  }

  getBeers(includeTapDetails:boolean = false): Observable<Beer[]> {
    const url = `${this.apiBaseUrl}/beers${includeTapDetails ? "?include_tap_details" : ""}`;
    return this.http.get<Beer[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createBeer(data: any): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers`;
    return this.http.post<Beer>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  getBeer(beerId: string, includeTapDetails:boolean = false): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers/${beerId}${includeTapDetails ? "?include_tap_details" : ""}`;
    return this.http.get<Beer>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteBeer(beerId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.delete<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateBeer(beerId: string, data: any): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.patch<Beer>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  getSensors(locationId?: string): Observable<Sensor[]> {
    var url: string;
    if (_.isNil(locationId)) {
      url = `${this.apiBaseUrl}/sensors`;
    } else {
      url = `${this.apiBaseUrl}/locations/${locationId}/sensors`;
    }

    return this.http.get<Sensor[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getSensor(sensorId: string): Observable<Sensor> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}`;
    return this.http.get<Sensor>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createSensor(data: any): Observable<Sensor> {
    const url = `${this.apiBaseUrl}/sensors`;
    return this.http.post<Sensor>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateSensor(sensorId: string, data: any): Observable<Sensor> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}`;
    return this.http.patch<Sensor>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteSensor(sensorId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}`;
    return this.http.delete<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getSensorType(): Observable<string[]> {
    const url = `${this.apiBaseUrl}/sensors/types`;
    return this.http.get<string[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getSensorData(sensorId: string, dataType: string): Observable<any> {
    const url = `${this.apiBaseUrl}/sensors/${sensorId}/${dataType}`;
    return this.http.get<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getPercentBeerRemaining(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "percent_beer_remaining");
  }

  getTotalBeerRemaining(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "total_beer_remaining");
  }

  getBeerRemainingUnit(sensorId: string): Observable<string> {
    return this.getSensorData(sensorId, "beer_remaining_unit");
  }

  getBeerStyle(sensorId: string): Observable<string> {
    return this.getSensorData(sensorId, "style");
  }

  getBeerOG(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "og");
  }

  getBeerFG(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "fg");
  }

  getBeerABV(sensorId: string): Observable<number> {
    return this.getSensorData(sensorId, "sbv");
  }

  getBeerFirmwareVersion(sensorId: string): Observable<string> {
    return this.getSensorData(sensorId, "firmware_version");
  }

  getCurrentUser(): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/current`;
    return this.http.get<UserInfo>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getUsers(): Observable<UserInfo[]> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.get<UserInfo[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getUser(userId: string): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.get<UserInfo>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createUser(data: any): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.post<UserInfo>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateUser(userId: string, data: object): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.patch<UserInfo>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteUser(userId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.delete<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getSettings(): Observable<Settings> {
    const url = `${this.apiBaseUrl}/settings`;
    return this.http.get<Settings>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  uploadImage(imageType: string, file: File): Observable<any> {
    const url = `${this.apiBaseUrl}/uploads/images/${imageType}`;
    const formData: FormData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(url, formData, {reportProgress: true}).pipe(catchError((err) => {return this.getError(err)}));
  }

  listImages(imageType: string): Observable<string[]> {
    const url = `${this.apiBaseUrl}/uploads/images/${imageType}`;
    return this.http.get<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  uploadBeerImage(file: File): Observable<any> {
    return this.uploadImage('beer', file);
  }

  uploadBeverageImage(file: File): Observable<any> {
    return this.uploadImage('beverage', file);
  }

  uploadUserImage(file: File): Observable<any> {
    return this.uploadImage('user', file);
  }

  getBeverages(includeTapDetails:boolean = false): Observable<Beverage[]> {
    const url = `${this.apiBaseUrl}/beverages${includeTapDetails ? "?include_tap_details" : ""}`;
    return this.http.get<Beverage[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createBeverage(data: any): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/beverages`;
    return this.http.post<Beverage>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  getBeverage(beverageId: string, includeTapDetails:boolean = false): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/beverages/${beverageId}${includeTapDetails ? "?include_tap_details" : ""}`;
    return this.http.get<Beverage>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteBeverage(beverageId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/beverages/${beverageId}`;
    return this.http.delete<any>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateBeverage(beverageId: string, data: any): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/beverages/${beverageId}`;
    return this.http.patch<Beverage>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }
}
