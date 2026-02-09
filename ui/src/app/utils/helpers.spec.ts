import { deepEqual, isObject, isNilOrEmpty, toBoolean, openFullscreen, closeFullscreen } from './helpers';

describe('helpers', () => {
  describe('isObject', () => {
    it('should return true for plain objects', () => {
      expect(isObject({})).toBe(true);
      expect(isObject({ a: 1 })).toBe(true);
    });

    it('should return true for arrays', () => {
      expect(isObject([])).toBe(true);
      expect(isObject([1, 2, 3])).toBe(true);
    });

    it('should return false for null', () => {
      expect(isObject(null)).toBe(false);
    });

    it('should return false for undefined', () => {
      expect(isObject(undefined)).toBe(false);
    });

    it('should return false for primitives', () => {
      expect(isObject('string')).toBe(false);
      expect(isObject(123)).toBe(false);
      expect(isObject(true)).toBe(false);
    });

    it('should return true for Date objects', () => {
      expect(isObject(new Date())).toBe(true);
    });
  });

  describe('deepEqual', () => {
    it('should return true for identical empty objects', () => {
      expect(deepEqual({}, {})).toBe(true);
    });

    it('should return true for identical simple objects', () => {
      expect(deepEqual({ a: 1, b: 2 }, { a: 1, b: 2 })).toBe(true);
    });

    it('should return false for objects with different keys', () => {
      expect(deepEqual({ a: 1 }, { b: 1 })).toBe(false);
    });

    it('should return false for objects with different values', () => {
      expect(deepEqual({ a: 1 }, { a: 2 })).toBe(false);
    });

    it('should return false for objects with different number of keys', () => {
      expect(deepEqual({ a: 1 }, { a: 1, b: 2 })).toBe(false);
    });

    it('should handle nested objects', () => {
      const obj1 = { a: { b: { c: 1 } } };
      const obj2 = { a: { b: { c: 1 } } };
      const obj3 = { a: { b: { c: 2 } } };

      expect(deepEqual(obj1, obj2)).toBe(true);
      expect(deepEqual(obj1, obj3)).toBe(false);
    });

    it('should handle mixed nested and primitive values', () => {
      const obj1 = { a: 1, b: { c: 2 }, d: 'string' };
      const obj2 = { a: 1, b: { c: 2 }, d: 'string' };
      const obj3 = { a: 1, b: { c: 3 }, d: 'string' };

      expect(deepEqual(obj1, obj2)).toBe(true);
      expect(deepEqual(obj1, obj3)).toBe(false);
    });

    it('should handle arrays as values', () => {
      // Note: Arrays are treated as objects, so this tests index-based comparison
      expect(deepEqual({ a: [1, 2] }, { a: [1, 2] })).toBe(true);
      expect(deepEqual({ a: [1, 2] }, { a: [1, 3] })).toBe(false);
    });
  });

  describe('isNilOrEmpty', () => {
    it('should return true for null', () => {
      expect(isNilOrEmpty(null)).toBe(true);
    });

    it('should return true for undefined', () => {
      expect(isNilOrEmpty(undefined)).toBe(true);
    });

    it('should return true for empty string', () => {
      expect(isNilOrEmpty('')).toBe(true);
    });

    it('should return false for non-empty string', () => {
      expect(isNilOrEmpty('hello')).toBe(false);
    });

    it('should return true for empty array', () => {
      expect(isNilOrEmpty([])).toBe(true);
    });

    it('should return false for non-empty array', () => {
      expect(isNilOrEmpty([1, 2, 3])).toBe(false);
    });

    it('should return true for empty object', () => {
      expect(isNilOrEmpty({})).toBe(true);
    });

    it('should return false for non-empty object', () => {
      expect(isNilOrEmpty({ a: 1 })).toBe(false);
    });

    it('should return false for boolean true', () => {
      expect(isNilOrEmpty(true)).toBe(false);
    });

    it('should return false for boolean false', () => {
      expect(isNilOrEmpty(false)).toBe(false);
    });

    it('should return true for NaN', () => {
      expect(isNilOrEmpty(NaN)).toBe(true);
    });

    it('should return false for valid numbers including zero', () => {
      expect(isNilOrEmpty(0)).toBe(false);
      expect(isNilOrEmpty(42)).toBe(false);
      expect(isNilOrEmpty(-1)).toBe(false);
    });
  });

  describe('toBoolean', () => {
    it('should return true for boolean true', () => {
      expect(toBoolean(true)).toBe(true);
    });

    it('should return false for boolean false', () => {
      expect(toBoolean(false)).toBe(false);
    });

    it('should return true for string "true"', () => {
      expect(toBoolean('true')).toBe(true);
      expect(toBoolean('TRUE')).toBe(true);
      expect(toBoolean('True')).toBe(true);
    });

    it('should return true for positive numbers', () => {
      expect(toBoolean(1)).toBe(true);
      expect(toBoolean(42)).toBe(true);
      expect(toBoolean(0.5)).toBe(true);
    });

    it('should return false for zero', () => {
      expect(toBoolean(0)).toBe(false);
    });

    it('should return false for negative numbers', () => {
      expect(toBoolean(-1)).toBe(false);
      expect(toBoolean(-100)).toBe(false);
    });

    it('should return false for null and undefined', () => {
      expect(toBoolean(null)).toBe(false);
      expect(toBoolean(undefined)).toBe(false);
    });

    it('should return false for empty objects and arrays', () => {
      expect(toBoolean({})).toBe(false);
      expect(toBoolean([])).toBe(false);
    });
  });

  describe('openFullscreen', () => {
    it('should call requestFullscreen when available', () => {
      const mockRequestFullscreen = jasmine.createSpy('requestFullscreen');
      const mockDocument = {
        documentElement: {
          requestFullscreen: mockRequestFullscreen,
        },
      } as unknown as Document;

      openFullscreen(mockDocument);

      expect(mockRequestFullscreen).toHaveBeenCalled();
    });

    it('should call mozRequestFullScreen when requestFullscreen is not available', () => {
      const mockMozRequestFullScreen = jasmine.createSpy('mozRequestFullScreen');
      const mockDocument = {
        documentElement: {
          mozRequestFullScreen: mockMozRequestFullScreen,
        },
      } as unknown as Document;

      openFullscreen(mockDocument);

      expect(mockMozRequestFullScreen).toHaveBeenCalled();
    });

    it('should call webkitRequestFullscreen when others are not available', () => {
      const mockWebkitRequestFullscreen = jasmine.createSpy('webkitRequestFullscreen');
      const mockDocument = {
        documentElement: {
          webkitRequestFullscreen: mockWebkitRequestFullscreen,
        },
      } as unknown as Document;

      openFullscreen(mockDocument);

      expect(mockWebkitRequestFullscreen).toHaveBeenCalled();
    });

    it('should call msRequestFullscreen when others are not available', () => {
      const mockMsRequestFullscreen = jasmine.createSpy('msRequestFullscreen');
      const mockDocument = {
        documentElement: {
          msRequestFullscreen: mockMsRequestFullscreen,
        },
      } as unknown as Document;

      openFullscreen(mockDocument);

      expect(mockMsRequestFullscreen).toHaveBeenCalled();
    });
  });

  describe('closeFullscreen', () => {
    it('should call exitFullscreen when available', () => {
      const mockExitFullscreen = jasmine.createSpy('exitFullscreen');
      const mockDocument = {
        exitFullscreen: mockExitFullscreen,
      } as unknown as Document;

      closeFullscreen(mockDocument);

      expect(mockExitFullscreen).toHaveBeenCalled();
    });

    it('should call mozCancelFullScreen when exitFullscreen is not available', () => {
      const mockMozCancelFullScreen = jasmine.createSpy('mozCancelFullScreen');
      const mockDocument = {
        mozCancelFullScreen: mockMozCancelFullScreen,
      } as unknown as Document;

      closeFullscreen(mockDocument);

      expect(mockMozCancelFullScreen).toHaveBeenCalled();
    });

    it('should call webkitExitFullscreen when others are not available', () => {
      const mockWebkitExitFullscreen = jasmine.createSpy('webkitExitFullscreen');
      const mockDocument = {
        webkitExitFullscreen: mockWebkitExitFullscreen,
      } as unknown as Document;

      closeFullscreen(mockDocument);

      expect(mockWebkitExitFullscreen).toHaveBeenCalled();
    });

    it('should call msExitFullscreen when others are not available', () => {
      const mockMsExitFullscreen = jasmine.createSpy('msExitFullscreen');
      const mockDocument = {
        msExitFullscreen: mockMsExitFullscreen,
      } as unknown as Document;

      closeFullscreen(mockDocument);

      expect(mockMsExitFullscreen).toHaveBeenCalled();
    });
  });
});
