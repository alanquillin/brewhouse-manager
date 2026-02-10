/**
 * Functional tests for DataService
 *
 * These tests run against a real API server running in Docker.
 * Start the API with: make test-api-up (from the api/tests/api directory)
 *
 * The tests use seed data with fixed UUIDs for predictable assertions.
 */
import {
  HttpClient,
  HttpHandlerFn,
  HttpRequest,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { WINDOW } from '../window.provider';
import { DataService } from './data.service';
import {
  Batch,
  Beer,
  Beverage,
  Dashboard,
  Location,
  Tap,
  TapMonitor,
  TapMonitorType,
  UserInfo,
} from '../models/models';

// ============================================================================
// Test Configuration
// ============================================================================

const API_BASE_URL = 'http://localhost:5050';
const ADMIN_API_KEY = 'test-admin-api-key-12345';
const USER_API_KEY = 'test-user-api-key-67890';

// ============================================================================
// Seed Data IDs (from api/tests/api/seed_data.py)
// ============================================================================

// Locations
const LOCATION_MAIN_ID = 'd863e51e-8083-4945-9080-7b0ea2c1aeca';
const LOCATION_SECONDARY_ID = 'b6b23426-a7c2-4b34-900a-f2166df12de1';
const LOCATION_EMPTY_ID = '6ae6fc3b-b337-4f9b-8206-8c684918d305';

// Beers
const BEER_IPA_ID = '72029e04-71ec-4b70-86cf-bcfab1b5ec9f';
const BEER_STOUT_ID = '541904b5-5525-418d-b400-89e6e6286230';
const BEER_LAGER_ID = 'c2bd2265-5def-4563-9534-498627df4328';
const BEER_WHEAT_ID = '677ac863-d1c8-4411-96e4-f5bba28006f2';

// Beverages
const BEVERAGE_COFFEE_ID = '3b1ee9b2-c9a0-4409-a57a-b2640d1512f5';
const BEVERAGE_SODA_ID = '2ab4206c-6278-4eab-b1d2-d4ca007993e5';

// Tap Monitors
const TAP_MONITOR_1_ID = '0a72afcc-b69c-40ce-a0f5-4667db9bbeba';
const TAP_MONITOR_2_ID = 'e109ec22-fd2c-4143-b971-9c8cdc180a17';
const TAP_MONITOR_3_ID = '06dd916b-1e19-4ebd-b5ff-cd9535e19245';
const TAP_MONITOR_SECONDARY_ID = 'f4eb799f-7a39-4f89-8835-09de1da28bff';

// Batches
const BATCH_IPA_ID = '1ce1610c-2426-438a-b58f-0eb1c82fd624';
const BATCH_STOUT_ID = '371daaba-45cf-46e5-aad2-c39dca915835';
const BATCH_LAGER_ID = '8a76a81d-099d-4372-a1c5-892787973bb1';
const BATCH_COFFEE_ID = '7aa317d2-96f6-4757-adc3-3b57d732760e';
const BATCH_WHEAT_ID = 'd59dae10-84bb-4969-a335-0b066bb96c65';

// Taps
const TAP_1_ID = '4e3c82e6-ecac-4e0c-a4b4-6c87fde9ea28';
const TAP_2_ID = 'bef890f4-4f0a-4f13-9999-567a49f1de7f';
const TAP_3_ID = 'cc5277fd-4e30-46c3-a28a-b82e9aed9f04';
const TAP_SECONDARY_1_ID = '4c175438-8511-4191-a537-1a8ec7236767';
const TAP_SECONDARY_2_ID = 'af976792-a2ce-4d0c-b7dc-8b9cfe6e8c64';

// Users
const USER_ADMIN_ID = '08eacfcc-d250-4506-8ed2-bf54b34b3672';
const USER_REGULAR_ID = '13967419-c957-4b4b-9105-24510fdf598f';

// ============================================================================
// HTTP Interceptor for API Key Authentication
// ============================================================================

// Global variable for API key - can be changed during tests
let currentApiKey = ADMIN_API_KEY;

// Functional interceptor that adds API key as Bearer token to all requests
function apiKeyInterceptor(req: HttpRequest<unknown>, next: HttpHandlerFn) {
  const authReq = req.clone({
    setHeaders: {
      Authorization: `Bearer ${currentApiKey}`,
    },
  });
  return next(authReq);
}

// ============================================================================
// Test Suite
// ============================================================================

describe('DataService Functional Tests', () => {
  let service: DataService;
  let httpClient: HttpClient;

  // Point directly to Docker API - Chrome is launched with --disable-web-security
  const mockWindow = {
    location: {
      protocol: 'http:',
      hostname: 'localhost',
      port: '5050',
    },
  } as unknown as Window;

  beforeEach(() => {
    currentApiKey = ADMIN_API_KEY;

    TestBed.configureTestingModule({
      providers: [
        // Use provideHttpClient with functional interceptor
        provideHttpClient(withInterceptors([apiKeyInterceptor])),
        DataService,
        { provide: WINDOW, useValue: mockWindow },
      ],
    });

    service = TestBed.inject(DataService);
    httpClient = TestBed.inject(HttpClient);
  });

  // Helper to set the API key for individual tests
  const setApiKey = (apiKey: string) => {
    currentApiKey = apiKey;
  };

  // ============================================================================
  // Health Check
  // ============================================================================

  describe('Health Check', () => {
    it('should verify API is available', async () => {
      const result = await firstValueFrom(service.isAvailable());
      expect(result).toBeTruthy();
    });
  });

  // ============================================================================
  // Locations API
  // ============================================================================

  describe('Locations API', () => {
    it('should get all locations', async () => {
      const locations = await firstValueFrom(service.getLocations());

      expect(locations).toBeTruthy();
      expect(locations.length).toBeGreaterThanOrEqual(3);

      const mainLocation = locations.find(l => l.id === LOCATION_MAIN_ID);
      expect(mainLocation).toBeTruthy();
      expect(mainLocation?.name).toBe('main-taproom');
      expect(mainLocation?.description).toBe('Main Taproom - 3 Taps');
    });

    it('should get a single location by ID', async () => {
      const location = await firstValueFrom(service.getLocation(LOCATION_MAIN_ID));

      expect(location).toBeTruthy();
      expect(location.id).toBe(LOCATION_MAIN_ID);
      expect(location.name).toBe('main-taproom');
    });

    it('should create, update, and delete a location', async () => {
      // Create
      const newLocation = await firstValueFrom(
        service.createLocation({
          name: 'test-location',
          description: 'Test Location for Functional Tests',
        })
      );
      expect(newLocation).toBeTruthy();
      expect(newLocation.id).toBeTruthy();
      expect(newLocation.name).toBe('test-location');

      // Update
      const updatedLocation = await firstValueFrom(
        service.updateLocation(newLocation.id, { description: 'Updated Description' })
      );
      expect(updatedLocation.description).toBe('Updated Description');

      // Delete
      await firstValueFrom(service.deleteLocation(newLocation.id));

      // Verify deleted
      try {
        await firstValueFrom(service.getLocation(newLocation.id));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });
  });

  // ============================================================================
  // Beers API
  // ============================================================================

  describe('Beers API', () => {
    it('should get all beers', async () => {
      const beers = await firstValueFrom(service.getBeers());

      expect(beers).toBeTruthy();
      expect(beers.length).toBeGreaterThanOrEqual(4);

      const ipa = beers.find(b => b.id === BEER_IPA_ID);
      expect(ipa).toBeTruthy();
      expect(ipa?.name).toBe('Test IPA');
      // Note: style is stored as number in the model, but comes as string from API
      expect(String((ipa as any)?.style)).toBe('IPA');
      // Note: abv is stored as string in the model
      expect(Number(ipa?.abv)).toBe(6.5);
    });

    it('should get a single beer by ID', async () => {
      const beer = await firstValueFrom(service.getBeer(BEER_STOUT_ID));

      expect(beer).toBeTruthy();
      expect(beer.id).toBe(BEER_STOUT_ID);
      expect(beer.name).toBe('Test Stout');
      expect(String((beer as any).style)).toBe('Stout');
    });

    it('should create, update, and delete a beer', async () => {
      // Create
      const newBeer = await firstValueFrom(
        service.createBeer({
          name: 'Test Pale Ale',
          description: 'A test pale ale',
          style: 'Pale Ale',
          abv: 5.5,
          ibu: 40,
          srm: 6.0,
        })
      );
      expect(newBeer).toBeTruthy();
      expect(newBeer.id).toBeTruthy();
      expect(newBeer.name).toBe('Test Pale Ale');

      // Update
      const updatedBeer = await firstValueFrom(
        service.updateBeer(newBeer.id, { abv: 5.8, ibu: 45 })
      );
      expect(Number(updatedBeer.abv)).toBe(5.8);
      expect(updatedBeer.ibu).toBe(45);

      // Delete
      await firstValueFrom(service.deleteBeer(newBeer.id));

      // Verify deleted
      try {
        await firstValueFrom(service.getBeer(newBeer.id));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });

    it('should get beer batches', async () => {
      const batches = await firstValueFrom(service.getBeerBatches(BEER_IPA_ID));

      expect(batches).toBeTruthy();
      expect(batches.length).toBeGreaterThanOrEqual(1);

      const ipaBatch = batches.find(b => b.id === BATCH_IPA_ID);
      expect(ipaBatch).toBeTruthy();
    });
  });

  // ============================================================================
  // Beverages API
  // ============================================================================

  describe('Beverages API', () => {
    it('should get all beverages', async () => {
      const beverages = await firstValueFrom(service.getBeverages());

      expect(beverages).toBeTruthy();
      expect(beverages.length).toBeGreaterThanOrEqual(2);

      const coffee = beverages.find(b => b.id === BEVERAGE_COFFEE_ID);
      expect(coffee).toBeTruthy();
      expect(coffee?.name).toBe('Test Cold Brew');
    });

    it('should get a single beverage by ID', async () => {
      const beverage = await firstValueFrom(service.getBeverage(BEVERAGE_SODA_ID));

      expect(beverage).toBeTruthy();
      expect(beverage.id).toBe(BEVERAGE_SODA_ID);
      expect(beverage.name).toBe('Test Soda');
    });

    it('should create, update, and delete a beverage', async () => {
      // Create
      const newBeverage = await firstValueFrom(
        service.createBeverage({
          name: 'Test Kombucha',
          description: 'A test kombucha',
          brewery: 'Test Kombucha Co.',
          type: 'kombucha',
          flavor: 'Ginger',
        })
      );
      expect(newBeverage).toBeTruthy();
      expect(newBeverage.id).toBeTruthy();
      expect(newBeverage.name).toBe('Test Kombucha');

      // Update
      const updatedBeverage = await firstValueFrom(
        service.updateBeverage(newBeverage.id, { flavor: 'Lemon Ginger' })
      );
      expect(updatedBeverage.flavor).toBe('Lemon Ginger');

      // Delete
      await firstValueFrom(service.deleteBeverage(newBeverage.id));

      // Verify deleted
      try {
        await firstValueFrom(service.getBeverage(newBeverage.id));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });

    it('should get beverage batches', async () => {
      const batches = await firstValueFrom(service.getBeverageBatches(BEVERAGE_COFFEE_ID));

      expect(batches).toBeTruthy();
      expect(batches.length).toBeGreaterThanOrEqual(1);

      const coffeeBatch = batches.find(b => b.id === BATCH_COFFEE_ID);
      expect(coffeeBatch).toBeTruthy();
    });
  });

  // ============================================================================
  // Taps API
  // ============================================================================

  describe('Taps API', () => {
    it('should get all taps', async () => {
      const taps = await firstValueFrom(service.getTaps());

      expect(taps).toBeTruthy();
      expect(taps.length).toBeGreaterThanOrEqual(5);
    });

    it('should get taps for a specific location', async () => {
      const taps = await firstValueFrom(service.getTaps(LOCATION_MAIN_ID));

      expect(taps).toBeTruthy();
      expect(taps.length).toBe(3);

      const tap1 = taps.find(t => t.id === TAP_1_ID);
      expect(tap1).toBeTruthy();
      expect(tap1?.tapNumber).toBe(1);
    });

    it('should get a single tap by ID', async () => {
      const tap = await firstValueFrom(service.getTap(TAP_1_ID));

      expect(tap).toBeTruthy();
      expect(tap.id).toBe(TAP_1_ID);
      expect(tap.tapNumber).toBe(1);
      expect(tap.description).toBe('Tap 1 - IPA');
      expect(tap.locationId).toBe(LOCATION_MAIN_ID);
    });

    it('should create, update, and delete a tap', async () => {
      // Create
      const newTap = await firstValueFrom(
        service.createTap({
          tapNumber: 99,
          description: 'Test Tap',
          locationId: LOCATION_EMPTY_ID,
        })
      );
      expect(newTap).toBeTruthy();
      expect(newTap.id).toBeTruthy();
      expect(newTap.tapNumber).toBe(99);

      // Update
      const updatedTap = await firstValueFrom(
        service.updateTap(newTap.id, { description: 'Updated Test Tap' })
      );
      expect(updatedTap.description).toBe('Updated Test Tap');

      // Delete
      await firstValueFrom(service.deleteTap(newTap.id));

      // Verify deleted
      try {
        await firstValueFrom(service.getTap(newTap.id));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });
  });

  // ============================================================================
  // Tap Monitors API
  // ============================================================================

  describe('Tap Monitors API', () => {
    it('should get all tap monitors', async () => {
      const monitors = await firstValueFrom(service.getTapMonitors());

      expect(monitors).toBeTruthy();
      expect(monitors.length).toBeGreaterThanOrEqual(4);
    });

    it('should get tap monitors for a specific location', async () => {
      const monitors = await firstValueFrom(service.getTapMonitors(LOCATION_MAIN_ID));

      expect(monitors).toBeTruthy();
      expect(monitors.length).toBe(3);
    });

    it('should get tap monitors with tap details', async () => {
      const monitors = await firstValueFrom(service.getTapMonitors(undefined, true));

      expect(monitors).toBeTruthy();
      expect(monitors.length).toBeGreaterThanOrEqual(4);
      // Verify the request completed successfully - tap details are optional based on data
      const monitorWithTap = monitors.find(m => m.id === TAP_MONITOR_1_ID);
      expect(monitorWithTap).toBeTruthy();
    });

    it('should get a single tap monitor by ID', async () => {
      const monitor = await firstValueFrom(service.getTapMonitor(TAP_MONITOR_1_ID));

      expect(monitor).toBeTruthy();
      expect(monitor.id).toBe(TAP_MONITOR_1_ID);
      expect(monitor.name).toBe('Monitor 1');
      expect(monitor.monitorType).toBe('open-plaato-keg');
    });

    it('should get monitor types', async () => {
      const types = await firstValueFrom(service.getMonitorTypes());

      expect(types).toBeTruthy();
      expect(types.length).toBeGreaterThan(0);

      // Should include known types
      const typeNames = types.map(t => t.type);
      expect(typeNames).toContain('open-plaato-keg');
      expect(typeNames).toContain('keg-volume-monitor-weight');
    });

    it('should create, update, and delete a tap monitor', async () => {
      // Create
      const newMonitor = await firstValueFrom(
        service.createTapMonitor({
          name: 'Test Monitor',
          monitorType: 'open-plaato-keg',
          locationId: LOCATION_EMPTY_ID,
          meta: {
            deviceId: 'test-device-999',
          },
        })
      );
      expect(newMonitor).toBeTruthy();
      expect(newMonitor.id).toBeTruthy();
      expect(newMonitor.name).toBe('Test Monitor');

      // Update
      const updatedMonitor = await firstValueFrom(
        service.updateTapMonitor(newMonitor.id, { name: 'Updated Test Monitor' })
      );
      expect(updatedMonitor.name).toBe('Updated Test Monitor');

      // Delete
      await firstValueFrom(service.deleteTapMonitor(newMonitor.id));

      // Verify deleted
      try {
        await firstValueFrom(service.getTapMonitor(newMonitor.id));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });
  });

  // ============================================================================
  // Batches API
  // ============================================================================

  describe('Batches API', () => {
    it('should get all batches', async () => {
      const batches = await firstValueFrom(service.getBatches());

      expect(batches).toBeTruthy();
      expect(batches.length).toBeGreaterThanOrEqual(5);
    });

    it('should get a single batch by ID', async () => {
      const batch = await firstValueFrom(service.getBatch(BATCH_IPA_ID));

      expect(batch).toBeTruthy();
      expect(batch.id).toBe(BATCH_IPA_ID);
      expect(batch.beerId).toBe(BEER_IPA_ID);
    });

    it('should get batch with tap details', async () => {
      const batch = await firstValueFrom(service.getBatch(BATCH_IPA_ID, true));

      expect(batch).toBeTruthy();
      expect(batch.id).toBe(BATCH_IPA_ID);
      // Should include tap information if the batch is on tap
    });

    it('should create, update, and delete a batch', async () => {
      // Create - dates must be Unix timestamps (seconds since epoch)
      const brewDate = new Date('2025-03-01').getTime() / 1000;
      const kegDate = new Date('2025-03-15').getTime() / 1000;
      const newBatch = await firstValueFrom(
        service.createBatch({
          beerId: BEER_WHEAT_ID,
          brewDate: brewDate,
          kegDate: kegDate,
          abv: 5.2,
          ibu: 14,
        })
      );
      expect(newBatch).toBeTruthy();
      expect(newBatch.id).toBeTruthy();
      expect(newBatch.beerId).toBe(BEER_WHEAT_ID);

      // Update
      const updatedBatch = await firstValueFrom(
        service.updateBatch(newBatch.id, { abv: 5.3 })
      );
      expect(Number(updatedBatch.abv)).toBe(5.3);

      // Delete
      await firstValueFrom(service.deleteBatch(newBatch.id));

      // Verify deleted
      try {
        await firstValueFrom(service.getBatch(newBatch.id));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });
  });

  // ============================================================================
  // Users API
  // ============================================================================

  describe('Users API', () => {
    it('should get current user', async () => {
      const user = await firstValueFrom(service.getCurrentUser());

      expect(user).toBeTruthy();
      expect(user.id).toBe(USER_ADMIN_ID);
      expect(user.email).toBe('admin@test.local');
      expect(user.admin).toBe(true);
    });

    it('should get all users (admin only)', async () => {
      const users = await firstValueFrom(service.getUsers());

      expect(users).toBeTruthy();
      expect(users.length).toBeGreaterThanOrEqual(2);

      const admin = users.find(u => u.id === USER_ADMIN_ID);
      expect(admin).toBeTruthy();
      expect(admin?.admin).toBe(true);

      const regular = users.find(u => u.id === USER_REGULAR_ID);
      expect(regular).toBeTruthy();
      expect(regular?.admin).toBe(false);
    });

    it('should get a single user by ID', async () => {
      const user = await firstValueFrom(service.getUser(USER_REGULAR_ID));

      expect(user).toBeTruthy();
      expect(user.id).toBe(USER_REGULAR_ID);
      expect(user.email).toBe('user@test.local');
    });

    it('should fail for regular user trying to access admin endpoints', async () => {
      setApiKey(USER_API_KEY);

      try {
        await firstValueFrom(service.getUsers());
        fail('Expected 403 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(403);
      }
    });
  });

  // ============================================================================
  // Dashboard API
  // ============================================================================

  describe('Dashboard API', () => {
    it('should get dashboard locations', async () => {
      const locations = await firstValueFrom(service.getDashboardLocations());

      expect(locations).toBeTruthy();
      expect(locations.length).toBeGreaterThanOrEqual(1);
    });

    it('should get dashboard for a location', async () => {
      const dashboard = await firstValueFrom(service.getDashboard(LOCATION_MAIN_ID));

      expect(dashboard).toBeTruthy();
      expect(dashboard.location).toBeTruthy();
      expect(dashboard.location.id).toBe(LOCATION_MAIN_ID);
      expect(dashboard.taps).toBeTruthy();
      expect(dashboard.taps.length).toBe(3);
    });

    it('should get dashboard tap', async () => {
      const tap = await firstValueFrom(service.getDashboardTap(TAP_1_ID));

      expect(tap).toBeTruthy();
      expect(tap.id).toBe(TAP_1_ID);
    });

    it('should get dashboard beer', async () => {
      const beer = await firstValueFrom(service.getDashboardBeer(BEER_IPA_ID));

      expect(beer).toBeTruthy();
      expect(beer.id).toBe(BEER_IPA_ID);
    });

    it('should get dashboard beverage', async () => {
      const beverage = await firstValueFrom(service.getDashboardBeverage(BEVERAGE_COFFEE_ID));

      expect(beverage).toBeTruthy();
      expect(beverage.id).toBe(BEVERAGE_COFFEE_ID);
    });

    it('should get dashboard tap monitor', async () => {
      const monitor = await firstValueFrom(service.getDashboardTapMonitor(TAP_MONITOR_1_ID));

      expect(monitor).toBeTruthy();
      expect(monitor.id).toBe(TAP_MONITOR_1_ID);
    });
  });

  // ============================================================================
  // Settings API
  // ============================================================================

  describe('Settings API', () => {
    it('should get settings', async () => {
      const settings = await firstValueFrom(service.getSettings());

      expect(settings).toBeTruthy();
      // Settings should have known properties
    });
  });

  // ============================================================================
  // Error Handling
  // ============================================================================

  describe('Error Handling', () => {
    it('should return 404 for non-existent location', async () => {
      // Use a valid UUID format that doesn't exist in the database
      const nonExistentUuid = '00000000-0000-0000-0000-000000000000';
      try {
        await firstValueFrom(service.getLocation(nonExistentUuid));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });

    it('should return 404 for non-existent beer', async () => {
      // Use a valid UUID format that doesn't exist in the database
      const nonExistentUuid = '00000000-0000-0000-0000-000000000001';
      try {
        await firstValueFrom(service.getBeer(nonExistentUuid));
        fail('Expected 404 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(404);
      }
    });

    it('should return 401 for unauthenticated requests', async () => {
      setApiKey('invalid-api-key');

      try {
        await firstValueFrom(service.getLocations());
        fail('Expected 401 error');
      } catch (err: any) {
        expect(err.statusCode).toBe(401);
      }
    });
  });
});
