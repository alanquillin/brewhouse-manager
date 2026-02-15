// since these will often be python API driven snake_case names

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { EventEmitter, Inject, Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import {
  Batch,
  Beer,
  Beverage,
  Dashboard,
  Location,
  PlaatoKegDevice,
  Settings,
  Tap,
  TapMonitor,
  TapMonitorData,
  TapMonitorDiscoveryData,
  TapMonitorType,
  UserInfo,
} from '../models/models';
import { isNilOrEmpty } from '../utils/helpers';
import { WINDOW } from '../window.provider';

import * as _ from 'lodash';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
};

export class DataError extends Error {
  statusCode!: number;
  statusText!: string;
  reason!: string;

  constructor(
    message?: string,
    statusCode?: any | undefined,
    statusText?: any | undefined,
    reason?: any | undefined
  ) {
    super(message);
    if (statusCode !== undefined) {
      this.statusCode = statusCode;
    }
    if (statusText !== undefined) {
      this.statusText = statusText;
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
  unauthorized: EventEmitter<DataError>;

  apiBaseUrl: string;
  baseUrl: string;

  constructor(
    public http: HttpClient,
    @Inject(WINDOW) private window: Window
  ) {
    this.unauthorized = new EventEmitter();

    const protocol = this.window.location.protocol;
    const hostname = this.window.location.hostname;
    const port = this.window.location.port;
    this.baseUrl = `${protocol}//${hostname}`;

    if (!((protocol === 'http:' && port === '80') || (protocol === 'https:' && port === '443'))) {
      this.baseUrl = `${this.baseUrl}:${port}`;
    }

    this.apiBaseUrl = this.baseUrl + '/api/v1';
  }

  getError(error: any, ignoreUnauthorized = false) {
    const errObj = new DataError(error.error.message);
    if (!(error.error instanceof ErrorEvent)) {
      // handle server-side errors
      errObj.reason = error.message;
      errObj.statusCode = _.toInteger(error.status);
      errObj.statusText = error.statusText;

      if (errObj.statusCode === 401 && !ignoreUnauthorized) {
        this.unauthorized.emit(errObj);
      }

      // This is a work around in case the browser got a 302 to redirect to the login page, but the original
      // request was not a GET so it tried to make an invalid request to /login instead of redirecting to the page
      if (
        errObj.statusCode === 405 &&
        !isNilOrEmpty(error.url) &&
        _.startsWith(error.url, `${this.baseUrl}/login`)
      ) {
        window.location.href = error.url;
      }
    }
    return throwError(() => {
      return errObj;
    });
  }

  login(email: string, password: string): Observable<any> {
    const url = `${this.baseUrl}/login`;
    return this.http
      .post<any>(url, { email, password }, httpOptions)
      .pipe(catchError((err: any) => this.getError(err)));
  }

  getLocations(): Observable<Location[]> {
    const url = `${this.apiBaseUrl}/locations`;
    return this.http.get<Location[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getLocation(location: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.get<Location>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createLocation(data: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations`;
    return this.http.post<Location>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteLocation(location: string): Observable<any> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateLocation(location: string, data: any): Observable<Location> {
    const url = `${this.apiBaseUrl}/locations/${location}`;
    return this.http.patch<Location>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getTaps(locationId?: string): Observable<Tap[]> {
    let url: string;
    if (_.isNil(locationId)) {
      url = `${this.apiBaseUrl}/taps`;
    } else {
      url = `${this.apiBaseUrl}/locations/${locationId}/taps`;
    }

    return this.http.get<Tap[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getTap(tapId: string): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.get<Tap>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createTap(data: any): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps`;
    return this.http.post<Tap>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateTap(tapId: string, data: any): Observable<Tap> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.patch<Tap>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteTap(tapId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/taps/${tapId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  clearBeerFromTap(tapId: string): Observable<any> {
    return this.clearTap(tapId);
  }

  clearBeverageFromTap(tapId: string): Observable<any> {
    return this.clearTap(tapId);
  }

  clearTap(tapId: string): Observable<any> {
    return this.updateTap(tapId, { batchId: null });
  }

  getBeers(): Observable<Beer[]> {
    const url = `${this.apiBaseUrl}/beers`;
    return this.http.get<Beer[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createBeer(data: any): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers`;
    return this.http.post<Beer>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getBeer(beerId: string): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.get<Beer>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteBeer(beerId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateBeer(beerId: string, data: any): Observable<Beer> {
    const url = `${this.apiBaseUrl}/beers/${beerId}`;
    return this.http.patch<Beer>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getTapMonitors(locationId?: string, includeTapDetails = false): Observable<TapMonitor[]> {
    let url: string;
    if (_.isNil(locationId)) {
      url = `${this.apiBaseUrl}/tap_monitors`;
    } else {
      url = `${this.apiBaseUrl}/locations/${locationId}/tap_monitors`;
    }

    const params = [];
    if (includeTapDetails) params.push('include_tap_details=true');
    const queryString = params.length > 0 ? `?${params.join('&')}` : '';
    url = `${url}${queryString}`;

    return this.http.get<TapMonitor[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getTapMonitor(tapMonitorId: string, includeTapDetails = false): Observable<TapMonitor> {
    const params = [];
    if (includeTapDetails) params.push('include_tap_details=true');
    const queryString = params.length > 0 ? `?${params.join('&')}` : '';

    const url = `${this.apiBaseUrl}/tap_monitors/${tapMonitorId}${queryString}`;
    return this.http.get<TapMonitor>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createTapMonitor(data: any): Observable<TapMonitor> {
    const url = `${this.apiBaseUrl}/tap_monitors`;
    return this.http.post<TapMonitor>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateTapMonitor(tapMonitorId: string, data: any): Observable<TapMonitor> {
    const url = `${this.apiBaseUrl}/tap_monitors/${tapMonitorId}`;
    return this.http.patch<TapMonitor>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteTapMonitor(tapMonitorId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/tap_monitors/${tapMonitorId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getMonitorTypes(): Observable<TapMonitorType[]> {
    const url = `${this.apiBaseUrl}/tap_monitors/types`;
    return this.http.get<TapMonitorType[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getAllTapMonitorData(tapMonitorId: string): Observable<TapMonitorData> {
    const url = `${this.apiBaseUrl}/tap_monitors/${tapMonitorId}/data`;
    return this.http.get<TapMonitorData>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getTapMonitorData(tapMonitorId: string, dataType: string): Observable<any> {
    const url = `${this.apiBaseUrl}/tap_monitors/${tapMonitorId}/data/${dataType}`;
    return this.http.get<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getPercentBeerRemaining(tapMonitorId: string): Observable<number> {
    return this.getTapMonitorData(tapMonitorId, 'percent_beer_remaining');
  }

  getTotalBeerRemaining(tapMonitorId: string): Observable<number> {
    return this.getTapMonitorData(tapMonitorId, 'total_beer_remaining');
  }

  getBeerRemainingUnit(tapMonitorId: string): Observable<string> {
    return this.getTapMonitorData(tapMonitorId, 'beer_remaining_unit');
  }

  getTapMonitorFirmwareVersion(tapMonitorId: string): Observable<string> {
    return this.getTapMonitorData(tapMonitorId, 'firmware_version');
  }

  discoverTapMonitors(monitorType: string): Observable<TapMonitorDiscoveryData[]> {
    const url = `${this.apiBaseUrl}/tap_monitors/discover/${monitorType}`;
    return this.http.get<TapMonitorDiscoveryData[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  // Plaato Keg Device Management API methods
  getPlaatoKegDevices(): Observable<PlaatoKegDevice[]> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg`;
    return this.http.get<PlaatoKegDevice[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getPlaatoKegDevice(deviceId: string): Observable<PlaatoKegDevice> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}`;
    return this.http.get<PlaatoKegDevice>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getPlaatoKegConnectedDevices(): Observable<string[]> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/connected`;
    return this.http.get<string[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createPlaatoKegDevice(data: any): Observable<PlaatoKegDevice> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg`;
    return this.http.post<any>(url, data, httpOptions).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updatePlaatoKegDevice(deviceId: string, data: any): Observable<any> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}`;
    return this.http.patch<any>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deletePlaatoKegDevice(deviceId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  resetKegtronPort(
    deviceId: string,
    portNum: number,
    data: any,
    params?: { [key: string]: string }
  ): Observable<boolean> {
    const url = `${this.apiBaseUrl}/devices/kegtron/${deviceId}/${portNum}`;
    const options = params ? { ...httpOptions, params } : httpOptions;
    return this.http.post<boolean>(url, data, options).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  setPlaatoKegMode(deviceId: string, mode: string): Observable<any> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}/set/mode`;
    return this.http.post<any>(url, { value: mode }, httpOptions).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  setPlaatoKegUnitType(deviceId: string, unitType: string): Observable<any> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}/set/unit_type`;
    return this.http.post<any>(url, { value: unitType }, httpOptions).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  setPlaatoKegUnitMode(deviceId: string, unitMode: string): Observable<any> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}/set/unit_mode`;
    return this.http.post<any>(url, { value: unitMode }, httpOptions).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  setPlaatoKegValue(deviceId: string, key: string, value: number): Observable<any> {
    const url = `${this.apiBaseUrl}/devices/plaato_keg/${deviceId}/set/${key}`;
    return this.http.post<any>(url, { value: value.toString() }, httpOptions).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getCurrentUser(ignoreUnauthorized = false): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/current`;
    return this.http.get<UserInfo>(url).pipe(
      catchError(err => {
        return this.getError(err, ignoreUnauthorized);
      })
    );
  }

  getUsers(): Observable<UserInfo[]> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.get<UserInfo[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getUser(userId: string): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.get<UserInfo>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createUser(data: any): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.post<UserInfo>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateUser(userId: string, data: object): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.patch<UserInfo>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteUser(userId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  generateUserAPIKey(userId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}/api_key/generate?regen=true`;
    return this.http.post<string>(url, {}).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteUserAPIKey(userId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}/api_key`;
    return this.http.delete<any>(url, {}).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateUserLocations(userId: string, data: any): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}/locations`;
    return this.http.post<any>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getSettings(): Observable<Settings> {
    const url = `${this.apiBaseUrl}/settings`;
    return this.http.get<Settings>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  uploadImage(imageType: string, file: File): Observable<any> {
    const url = `${this.apiBaseUrl}/uploads/images/${imageType}`;
    const formData: FormData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(url, formData, { reportProgress: true }).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  listImages(imageType: string): Observable<string[]> {
    const url = `${this.apiBaseUrl}/uploads/images/${imageType}`;
    return this.http.get<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
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

  getBeverages(includeTapDetails = false): Observable<Beverage[]> {
    const url = `${this.apiBaseUrl}/beverages${includeTapDetails ? '?include_tap_details' : ''}`;
    return this.http.get<Beverage[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createBeverage(data: any): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/beverages`;
    return this.http.post<Beverage>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getBeverage(beverageId: string, includeTapDetails = false): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/beverages/${beverageId}${includeTapDetails ? '?include_tap_details' : ''}`;
    return this.http.get<Beverage>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteBeverage(beverageId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/beverages/${beverageId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateBeverage(beverageId: string, data: any): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/beverages/${beverageId}`;
    return this.http.patch<Beverage>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteImageTransition(imageTransitionId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/image_transitions/${imageTransitionId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getDashboard(locationId: string): Observable<Dashboard> {
    const url = `${this.apiBaseUrl}/dashboard/locations/${locationId}`;
    return this.http.get<Dashboard>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getDashboardLocations(): Observable<Location[]> {
    const url = `${this.apiBaseUrl}/dashboard/locations`;
    return this.http.get<Location[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getDashboardTap(tapId: string): Observable<Tap> {
    const url = `${this.apiBaseUrl}/dashboard/taps/${tapId}`;
    return this.http.get<Tap>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getDashboardBeer(beerId: string): Observable<Beer> {
    const url = `${this.apiBaseUrl}/dashboard/beers/${beerId}`;
    return this.http.get<Beer>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getDashboardBeverage(beverageId: string): Observable<Beverage> {
    const url = `${this.apiBaseUrl}/dashboard/beverages/${beverageId}`;
    return this.http.get<Beverage>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getDashboardTapMonitor(tapMonitorId: string): Observable<TapMonitor> {
    const url = `${this.apiBaseUrl}/dashboard/tap_monitors/${tapMonitorId}`;
    return this.http.get<TapMonitor>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  isAvailable(): Observable<any> {
    const url = `${this.baseUrl}/health`;
    return this.http.get<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getBatches(): Observable<Batch[]> {
    const url = `${this.apiBaseUrl}/batches`;
    return this.http.get<Batch[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getBeerBatches(
    beerId: string,
    includeTapDetails = false,
    includeArchived = false
  ): Observable<Batch[]> {
    const params = [];
    if (includeTapDetails) params.push('include_tap_details=true');
    if (includeArchived) params.push('include_archived=true');
    const queryString = params.length > 0 ? `?${params.join('&')}` : '';
    const url = `${this.apiBaseUrl}/beers/${beerId}/batches${queryString}`;
    return this.http.get<Batch[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getBeverageBatches(
    beverageId: string,
    includeTapDetails = false,
    includeArchived = false
  ): Observable<Batch[]> {
    const params = [];
    if (includeTapDetails) params.push('include_tap_details=true');
    if (includeArchived) params.push('include_archived=true');
    const queryString = params.length > 0 ? `?${params.join('&')}` : '';
    const url = `${this.apiBaseUrl}/beverages/${beverageId}/batches${queryString}`;
    return this.http.get<Batch[]>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  createBatch(data: any): Observable<Batch> {
    const url = `${this.apiBaseUrl}/batches`;
    return this.http.post<Batch>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  getBatch(batchId: string, includeTapDetails = false): Observable<Batch> {
    const params = [];
    if (includeTapDetails) params.push('include_tap_details=true');
    const queryString = params.length > 0 ? `?${params.join('&')}` : '';
    const url = `${this.apiBaseUrl}/batches/${batchId}${queryString}`;
    return this.http.get<Batch>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  deleteBatch(batchId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/batches/${batchId}`;
    return this.http.delete<any>(url).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }

  updateBatch(batchId: string, data: any): Observable<Batch> {
    const url = `${this.apiBaseUrl}/batches/${batchId}`;
    return this.http.patch<Batch>(url, data).pipe(
      catchError(err => {
        return this.getError(err);
      })
    );
  }
}
