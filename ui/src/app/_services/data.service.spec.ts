import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { WINDOW } from '../window.provider';
import { DataError, DataService } from './data.service';

describe('DataService', () => {
  let service: DataService;
  let httpMock: HttpTestingController;
  let mockWindow: Window;

  const mockLocation = {
    protocol: 'https:',
    hostname: 'example.com',
    port: '443',
  };

  beforeEach(() => {
    mockWindow = {
      location: mockLocation,
    } as unknown as Window;

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [DataService, { provide: WINDOW, useValue: mockWindow }],
    });

    service = TestBed.inject(DataService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('constructor', () => {
    it('should set baseUrl correctly for https on port 443', () => {
      expect(service.baseUrl).toBe('https://example.com');
    });

    it('should set apiBaseUrl correctly', () => {
      expect(service.apiBaseUrl).toBe('https://example.com/api/v1');
    });

    it('should include port when not default', () => {
      TestBed.resetTestingModule();

      const customWindow = {
        location: { protocol: 'https:', hostname: 'example.com', port: '8443' },
      } as unknown as Window;

      TestBed.configureTestingModule({
        imports: [HttpClientTestingModule],
        providers: [DataService, { provide: WINDOW, useValue: customWindow }],
      });

      const customService = TestBed.inject(DataService);
      expect(customService.baseUrl).toBe('https://example.com:8443');
    });

    it('should not include port for http on port 80', () => {
      TestBed.resetTestingModule();

      const httpWindow = {
        location: { protocol: 'http:', hostname: 'example.com', port: '80' },
      } as unknown as Window;

      TestBed.configureTestingModule({
        imports: [HttpClientTestingModule],
        providers: [DataService, { provide: WINDOW, useValue: httpWindow }],
      });

      const httpService = TestBed.inject(DataService);
      expect(httpService.baseUrl).toBe('http://example.com');
    });

    it('should have unauthorized EventEmitter', () => {
      expect(service.unauthorized).toBeTruthy();
    });
  });

  describe('DataError class', () => {
    it('should create error with message', () => {
      const error = new DataError('Test error');
      expect(error.message).toBe('Test error');
    });

    it('should set statusCode', () => {
      const error = new DataError('Error', 404);
      expect(error.statusCode).toBe(404);
    });

    it('should set statusText', () => {
      const error = new DataError('Error', 404, 'Not Found');
      expect(error.statusText).toBe('Not Found');
    });

    it('should set reason', () => {
      const error = new DataError('Error', 404, 'Not Found', 'Resource not found');
      expect(error.reason).toBe('Resource not found');
    });

    it('should extend Error', () => {
      const error = new DataError('Test');
      expect(error instanceof Error).toBe(true);
    });
  });

  describe('getError', () => {
    it('should emit unauthorized for 401 errors', (done: DoneFn) => {
      service.unauthorized.subscribe(error => {
        expect(error.statusCode).toBe(401);
        done();
      });

      const mockError = {
        error: { message: 'Unauthorized' },
        status: 401,
        statusText: 'Unauthorized',
        message: 'HTTP error',
      };

      service.getError(mockError).subscribe({
        error: () => {},
      });
    });

    it('should not emit unauthorized when ignoreUnauthorized is true', () => {
      let emitted = false;
      service.unauthorized.subscribe(() => {
        emitted = true;
      });

      const mockError = {
        error: { message: 'Unauthorized' },
        status: 401,
        statusText: 'Unauthorized',
        message: 'HTTP error',
      };

      service.getError(mockError, true).subscribe({
        error: () => {},
      });

      expect(emitted).toBe(false);
    });

    it('should return DataError observable', (done: DoneFn) => {
      const mockError = {
        error: { message: 'Server Error' },
        status: 500,
        statusText: 'Internal Server Error',
        message: 'HTTP error',
      };

      service.getError(mockError).subscribe({
        error: err => {
          expect(err instanceof DataError).toBe(true);
          expect(err.message).toBe('Server Error');
          expect(err.statusCode).toBe(500);
          done();
        },
      });
    });
  });

  describe('login', () => {
    it('should POST to login endpoint', () => {
      service.login('test@example.com', 'password').subscribe();

      const req = httpMock.expectOne('https://example.com/login');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email: 'test@example.com', password: 'password' });
      req.flush({ success: true });
    });

    it('should handle login errors', (done: DoneFn) => {
      service.login('test@example.com', 'wrong').subscribe({
        error: err => {
          expect(err.statusCode).toBe(401);
          done();
        },
      });

      const req = httpMock.expectOne('https://example.com/login');
      req.flush({ message: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });
    });
  });

  describe('Locations API', () => {
    it('should GET all locations', () => {
      const mockLocations = [{ id: '1', name: 'Location 1' }];

      service.getLocations().subscribe(locations => {
        expect(locations.length).toBe(1);
        expect(locations[0].id).toBe('1');
        expect(locations[0].name).toBe('Location 1');
      });

      const req = httpMock.expectOne('https://example.com/api/v1/locations');
      expect(req.request.method).toBe('GET');
      req.flush(mockLocations);
    });

    it('should GET single location', () => {
      const mockLocationData = { id: '1', name: 'Location 1' };

      service.getLocation('1').subscribe(location => {
        expect(location.id).toBe('1');
        expect(location.name).toBe('Location 1');
      });

      const req = httpMock.expectOne('https://example.com/api/v1/locations/1');
      expect(req.request.method).toBe('GET');
      req.flush(mockLocationData);
    });

    it('should POST new location', () => {
      const newLocation = { name: 'New Location' };
      const createdLocation = { id: '1', name: 'New Location' };

      service.createLocation(newLocation).subscribe(location => {
        expect(location.id).toBe('1');
        expect(location.name).toBe('New Location');
      });

      const req = httpMock.expectOne('https://example.com/api/v1/locations');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newLocation);
      req.flush(createdLocation);
    });

    it('should DELETE location', () => {
      service.deleteLocation('1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/locations/1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should PATCH location', () => {
      const updateData = { name: 'Updated' };

      service.updateLocation('1', updateData).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/locations/1');
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(updateData);
      req.flush({ id: '1', ...updateData });
    });
  });

  describe('Taps API', () => {
    it('should GET all taps', () => {
      service.getTaps().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET taps for specific location', () => {
      service.getTaps('loc1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/locations/loc1/taps');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single tap', () => {
      service.getTap('tap1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps/tap1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should POST new tap', () => {
      const tapData = { name: 'Tap 1' };

      service.createTap(tapData).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH tap', () => {
      service.updateTap('tap1', { name: 'Updated' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps/tap1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE tap', () => {
      service.deleteTap('tap1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps/tap1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should clear beer from tap', () => {
      service.clearBeerFromTap('tap1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps/tap1');
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual({ batchId: null });
      req.flush({});
    });

    it('should clear beverage from tap', () => {
      service.clearBeverageFromTap('tap1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps/tap1');
      expect(req.request.body).toEqual({ batchId: null });
      req.flush({});
    });

    it('should clear tap', () => {
      service.clearTap('tap1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/taps/tap1');
      expect(req.request.body).toEqual({ batchId: null });
      req.flush({});
    });
  });

  describe('Beers API', () => {
    it('should GET all beers', () => {
      service.getBeers().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beers');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single beer', () => {
      service.getBeer('beer1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beers/beer1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should POST new beer', () => {
      service.createBeer({ name: 'IPA' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beers');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH beer', () => {
      service.updateBeer('beer1', { name: 'Updated IPA' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beers/beer1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE beer', () => {
      service.deleteBeer('beer1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beers/beer1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });
  });

  describe('Tap Monitors API', () => {
    it('should GET all tap monitors', () => {
      service.getTapMonitors().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET tap monitors for location', () => {
      service.getTapMonitors('loc1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/locations/loc1/tap_monitors');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET tap monitors with tap details', () => {
      service.getTapMonitors(undefined, true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors?include_tap_details=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET tap monitors for location with tap details', () => {
      service.getTapMonitors('loc1', true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/locations/loc1/tap_monitors?include_tap_details=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single tap monitor', () => {
      service.getTapMonitor('mon1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors/mon1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET tap monitor with tap details', () => {
      service.getTapMonitor('mon1', true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors/mon1?include_tap_details=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should POST new tap monitor', () => {
      service.createTapMonitor({ name: 'Monitor 1' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH tap monitor', () => {
      service.updateTapMonitor('mon1', { name: 'Updated' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors/mon1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE tap monitor', () => {
      service.deleteTapMonitor('mon1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors/mon1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should GET monitor types', () => {
      service.getMonitorTypes().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors/types');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET all tap monitor data', () => {
      service.getAllTapMonitorData('mon1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors/mon1/data');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET specific tap monitor data', () => {
      service.getTapMonitorData('mon1', 'temperature').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors/mon1/data/temperature'
      );
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET percent beer remaining', () => {
      service.getPercentBeerRemaining('mon1').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors/mon1/data/percent_beer_remaining'
      );
      expect(req.request.method).toBe('GET');
      req.flush(75);
    });

    it('should GET total beer remaining', () => {
      service.getTotalBeerRemaining('mon1').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors/mon1/data/total_beer_remaining'
      );
      expect(req.request.method).toBe('GET');
      req.flush(5.5);
    });

    it('should GET beer remaining unit', () => {
      service.getBeerRemainingUnit('mon1').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors/mon1/data/beer_remaining_unit'
      );
      expect(req.request.method).toBe('GET');
      req.flush('gallons');
    });

    it('should GET firmware version', () => {
      service.getTapMonitorFirmwareVersion('mon1').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/tap_monitors/mon1/data/firmware_version'
      );
      expect(req.request.method).toBe('GET');
      req.flush('1.0.0');
    });

    it('should discover tap monitors', () => {
      service.discoverTapMonitors('plaato').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/tap_monitors/discover/plaato');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });
  });

  describe('Plaato Keg Devices API', () => {
    it('should GET all plaato keg devices', () => {
      service.getPlaatoKegDevices().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single plaato keg device', () => {
      service.getPlaatoKegDevice('dev1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg/dev1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET connected devices', () => {
      service.getPlaatoKegConnectedDevices().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg/connected');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should POST new plaato keg device', () => {
      service.createPlaatoKegDevice({ name: 'Device 1' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH plaato keg device', () => {
      service.updatePlaatoKegDevice('dev1', { name: 'Updated' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg/dev1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE plaato keg device', () => {
      service.deletePlaatoKegDevice('dev1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg/dev1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should set plaato keg mode', () => {
      service.setPlaatoKegMode('dev1', 'beer').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg/dev1/set/mode');
      expect(req.request.body).toEqual({ value: 'beer' });
      req.flush({});
    });

    it('should set plaato keg unit type', () => {
      service.setPlaatoKegUnitType('dev1', 'metric').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/devices/plaato_keg/dev1/set/unit_type'
      );
      expect(req.request.body).toEqual({ value: 'metric' });
      req.flush({});
    });

    it('should set plaato keg unit mode', () => {
      service.setPlaatoKegUnitMode('dev1', 'volume').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/devices/plaato_keg/dev1/set/unit_mode'
      );
      expect(req.request.body).toEqual({ value: 'volume' });
      req.flush({});
    });

    it('should set plaato keg value', () => {
      service.setPlaatoKegValue('dev1', 'tare', 100).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/plaato_keg/dev1/set/tare');
      expect(req.request.body).toEqual({ value: '100' });
      req.flush({});
    });
  });

  describe('Users API', () => {
    it('should GET current user', () => {
      service.getCurrentUser().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/current');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET current user with ignoreUnauthorized', () => {
      service.getCurrentUser(true).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/current');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET all users', () => {
      service.getUsers().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single user', () => {
      service.getUser('user1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/user1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should POST new user', () => {
      service.createUser({ email: 'test@example.com' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH user', () => {
      service.updateUser('user1', { firstName: 'John' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/user1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE user', () => {
      service.deleteUser('user1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/user1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should generate user API key', () => {
      service.generateUserAPIKey('user1').subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/users/user1/api_key/generate?regen=true'
      );
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should DELETE user API key', () => {
      service.deleteUserAPIKey('user1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/user1/api_key');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should update user locations', () => {
      service.updateUserLocations('user1', { locations: ['loc1'] }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/users/user1/locations');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });
  });

  describe('Settings API', () => {
    it('should GET settings', () => {
      service.getSettings().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/settings');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });
  });

  describe('Image Upload API', () => {
    it('should upload image', () => {
      const file = new File(['content'], 'test.png', { type: 'image/png' });

      service.uploadImage('beer', file).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/uploads/images/beer');
      expect(req.request.method).toBe('POST');
      expect(req.request.body instanceof FormData).toBe(true);
      req.flush({});
    });

    it('should list images', () => {
      service.listImages('beer').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/uploads/images/beer');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should upload beer image', () => {
      const file = new File(['content'], 'beer.png', { type: 'image/png' });

      service.uploadBeerImage(file).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/uploads/images/beer');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should upload beverage image', () => {
      const file = new File(['content'], 'beverage.png', { type: 'image/png' });

      service.uploadBeverageImage(file).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/uploads/images/beverage');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should upload user image', () => {
      const file = new File(['content'], 'user.png', { type: 'image/png' });

      service.uploadUserImage(file).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/uploads/images/user');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });
  });

  describe('Beverages API', () => {
    it('should GET all beverages', () => {
      service.getBeverages().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beverages with tap details', () => {
      service.getBeverages(true).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages?include_tap_details');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single beverage', () => {
      service.getBeverage('bev1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages/bev1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET beverage with tap details', () => {
      service.getBeverage('bev1', true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/beverages/bev1?include_tap_details'
      );
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should POST new beverage', () => {
      service.createBeverage({ name: 'Cider' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH beverage', () => {
      service.updateBeverage('bev1', { name: 'Updated' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages/bev1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE beverage', () => {
      service.deleteBeverage('bev1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages/bev1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });
  });

  describe('Image Transitions API', () => {
    it('should DELETE image transition', () => {
      service.deleteImageTransition('trans1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/image_transitions/trans1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });
  });

  describe('Dashboard API', () => {
    it('should GET dashboard for location', () => {
      service.getDashboard('loc1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/dashboard/locations/loc1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET dashboard locations', () => {
      service.getDashboardLocations().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/dashboard/locations');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET dashboard tap', () => {
      service.getDashboardTap('tap1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/dashboard/taps/tap1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET dashboard beer', () => {
      service.getDashboardBeer('beer1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/dashboard/beers/beer1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET dashboard beverage', () => {
      service.getDashboardBeverage('bev1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/dashboard/beverages/bev1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET dashboard tap monitor', () => {
      service.getDashboardTapMonitor('mon1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/dashboard/tap_monitors/mon1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });
  });

  describe('Kegtron Device API', () => {
    it('should POST to reset kegtron port', () => {
      const data = { volumeSize: 5.0, volumeUnit: 'gal' };

      service.resetKegtronPort('dev-1', 0, data).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/kegtron/dev-1/0');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(data);
      req.flush(true);
    });

    it('should include update_date_tapped query param when true', () => {
      const data = { volumeSize: 5.0, volumeUnit: 'gal' };

      service.resetKegtronPort('dev-1', 0, data, true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/devices/kegtron/dev-1/0?update_date_tapped=true'
      );
      expect(req.request.method).toBe('POST');
      req.flush(true);
    });

    it('should not include query param when updateDateTapped is false', () => {
      const data = { volumeSize: 5.0, volumeUnit: 'gal' };

      service.resetKegtronPort('dev-1', 0, data, false).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/kegtron/dev-1/0');
      expect(req.request.method).toBe('POST');
      req.flush(true);
    });

    it('should not include query param when updateDateTapped is omitted', () => {
      const data = { volumeSize: 5.0, volumeUnit: 'gal' };

      service.resetKegtronPort('dev-1', 0, data).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/kegtron/dev-1/0');
      expect(req.request.method).toBe('POST');
      req.flush(true);
    });

    it('should handle kegtron port reset errors', (done: DoneFn) => {
      const data = { volumeSize: 5.0, volumeUnit: 'gal' };

      service.resetKegtronPort('dev-1', 0, data).subscribe({
        error: err => {
          expect(err.statusCode).toBe(502);
          done();
        },
      });

      const req = httpMock.expectOne('https://example.com/api/v1/devices/kegtron/dev-1/0');
      req.flush(
        { message: 'Failed to update kegtron device' },
        { status: 502, statusText: 'Bad Gateway' }
      );
    });

    it('should use correct port number in URL', () => {
      const data = { volumeSize: 19.0, volumeUnit: 'l' };

      service.resetKegtronPort('dev-2', 1, data).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/devices/kegtron/dev-2/1');
      expect(req.request.method).toBe('POST');
      req.flush(true);
    });
  });

  describe('Health API', () => {
    it('should check if available', () => {
      service.isAvailable().subscribe();

      const req = httpMock.expectOne('https://example.com/health');
      expect(req.request.method).toBe('GET');
      req.flush({ status: 'ok' });
    });
  });

  describe('Batches API', () => {
    it('should GET all batches', () => {
      service.getBatches().subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/batches');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beer batches', () => {
      service.getBeerBatches('beer1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beers/beer1/batches');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beer batches with tap details', () => {
      service.getBeerBatches('beer1', true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/beers/beer1/batches?include_tap_details=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beer batches with archived', () => {
      service.getBeerBatches('beer1', false, true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/beers/beer1/batches?include_archived=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beer batches with both options', () => {
      service.getBeerBatches('beer1', true, true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/beers/beer1/batches?include_tap_details=true&include_archived=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beverage batches', () => {
      service.getBeverageBatches('bev1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/beverages/bev1/batches');
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET beverage batches with options', () => {
      service.getBeverageBatches('bev1', true, true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/beverages/bev1/batches?include_tap_details=true&include_archived=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should GET single batch', () => {
      service.getBatch('batch1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/batches/batch1');
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should GET batch with tap details', () => {
      service.getBatch('batch1', true).subscribe();

      const req = httpMock.expectOne(
        'https://example.com/api/v1/batches/batch1?include_tap_details=true'
      );
      expect(req.request.method).toBe('GET');
      req.flush({});
    });

    it('should POST new batch', () => {
      service.createBatch({ beerId: 'beer1' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/batches');
      expect(req.request.method).toBe('POST');
      req.flush({});
    });

    it('should PATCH batch', () => {
      service.updateBatch('batch1', { notes: 'Updated' }).subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/batches/batch1');
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should DELETE batch', () => {
      service.deleteBatch('batch1').subscribe();

      const req = httpMock.expectOne('https://example.com/api/v1/batches/batch1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });
  });

  describe('error handling', () => {
    it('should handle network errors', (done: DoneFn) => {
      service.getLocations().subscribe({
        error: err => {
          expect(err).toBeTruthy();
          done();
        },
      });

      const req = httpMock.expectOne('https://example.com/api/v1/locations');
      req.flush({ message: 'Server error' }, { status: 500, statusText: 'Internal Server Error' });
    });

    it('should handle 404 errors', (done: DoneFn) => {
      service.getLocation('nonexistent').subscribe({
        error: err => {
          expect(err.statusCode).toBe(404);
          done();
        },
      });

      const req = httpMock.expectOne('https://example.com/api/v1/locations/nonexistent');
      req.flush({ message: 'Not found' }, { status: 404, statusText: 'Not Found' });
    });
  });
});
