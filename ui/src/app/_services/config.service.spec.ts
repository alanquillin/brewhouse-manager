import { TestBed } from '@angular/core/testing';

import { ConfigService } from './config.service';

describe('ConfigService', () => {
  let service: ConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ConfigService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('updated EventEmitter', () => {
    it('should have an updated EventEmitter', () => {
      expect(service.updated).toBeTruthy();
    });

    it('should emit events when subscribed', (done: DoneFn) => {
      const testData = { key: 'value' };

      service.updated.subscribe(data => {
        expect(data).toEqual(testData);
        done();
      });

      service.update(testData);
    });
  });

  describe('update', () => {
    it('should emit data through updated EventEmitter', (done: DoneFn) => {
      const testData = { test: 'data' };

      service.updated.subscribe(data => {
        expect(data).toEqual(testData);
        done();
      });

      service.update(testData);
    });

    it('should emit string data', (done: DoneFn) => {
      service.updated.subscribe(data => {
        expect(data).toBe('string data');
        done();
      });

      service.update('string data');
    });

    it('should emit null data', (done: DoneFn) => {
      service.updated.subscribe(data => {
        expect(data).toBeNull();
        done();
      });

      service.update(null);
    });

    it('should emit array data', (done: DoneFn) => {
      const arrayData = [1, 2, 3];

      service.updated.subscribe(data => {
        expect(data).toEqual(arrayData);
        done();
      });

      service.update(arrayData);
    });

    it('should emit complex nested objects', (done: DoneFn) => {
      const complexData = {
        level1: {
          level2: {
            value: 'deep',
          },
        },
        array: [1, 2, 3],
      };

      service.updated.subscribe(data => {
        expect(data).toEqual(complexData);
        done();
      });

      service.update(complexData);
    });
  });

  describe('multiple subscribers', () => {
    it('should notify all subscribers', () => {
      const results: any[] = [];
      const testData = { id: 1 };

      service.updated.subscribe(data => results.push({ subscriber: 1, data }));
      service.updated.subscribe(data => results.push({ subscriber: 2, data }));

      service.update(testData);

      expect(results.length).toBe(2);
      expect(results[0]).toEqual({ subscriber: 1, data: testData });
      expect(results[1]).toEqual({ subscriber: 2, data: testData });
    });
  });
});
