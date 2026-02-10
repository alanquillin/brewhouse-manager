import {
  convertUnixTimestamp,
  formatDate,
  fromJsTimestamp,
  fromUnixTimestamp,
  toJsTimestamp,
  toUnixTimestamp,
} from './datetime';

describe('datetime', () => {
  describe('formatDate', () => {
    it('should return null for null input', () => {
      expect(formatDate(null as unknown as Date)).toBeNull();
    });

    it('should return undefined for undefined input', () => {
      expect(formatDate(undefined as unknown as Date)).toBeUndefined();
    });

    it('should format a valid date', () => {
      const date = new Date('2024-03-15');
      const result = formatDate(date);

      // The exact format depends on locale, so just check it's a non-empty string
      expect(result).toBeDefined();
      expect(typeof result).toBe('string');
      expect(result!.length).toBeGreaterThan(0);
    });

    it('should format dates consistently', () => {
      const date1 = new Date('2024-01-01');
      const date2 = new Date('2024-01-01');

      expect(formatDate(date1)).toBe(formatDate(date2));
    });
  });

  describe('fromUnixTimestamp', () => {
    it('should convert Unix timestamp (seconds) to Date', () => {
      // Unix timestamp for 2024-01-01 00:00:00 UTC
      const unixTimestamp = 1704067200;
      const result = fromUnixTimestamp(unixTimestamp);

      expect(result instanceof Date).toBe(true);
      expect(result.getTime()).toBe(unixTimestamp * 1000);
    });

    it('should handle zero timestamp (Unix epoch)', () => {
      const result = fromUnixTimestamp(0);

      expect(result instanceof Date).toBe(true);
      expect(result.getTime()).toBe(0);
      expect(result.getUTCFullYear()).toBe(1970);
    });

    it('should handle negative timestamps (dates before Unix epoch)', () => {
      const negativeTimestamp = -86400; // One day before epoch
      const result = fromUnixTimestamp(negativeTimestamp);

      expect(result instanceof Date).toBe(true);
      expect(result.getTime()).toBe(-86400000);
    });
  });

  describe('fromJsTimestamp', () => {
    it('should convert JavaScript timestamp (milliseconds) to Date', () => {
      const jsTimestamp = 1704067200000; // 2024-01-01 00:00:00 UTC in ms
      const result = fromJsTimestamp(jsTimestamp);

      expect(result instanceof Date).toBe(true);
      expect(result.getTime()).toBe(jsTimestamp);
    });

    it('should handle zero timestamp', () => {
      const result = fromJsTimestamp(0);

      expect(result instanceof Date).toBe(true);
      expect(result.getTime()).toBe(0);
    });

    it('should handle current timestamp', () => {
      const now = Date.now();
      const result = fromJsTimestamp(now);

      expect(result.getTime()).toBe(now);
    });
  });

  describe('toJsTimestamp', () => {
    it('should convert Date to JavaScript timestamp (milliseconds)', () => {
      const date = new Date('2024-01-01T00:00:00Z');
      const result = toJsTimestamp(date);

      expect(typeof result).toBe('number');
      expect(result).toBe(date.getTime());
    });

    it('should return milliseconds since Unix epoch', () => {
      const epochDate = new Date(0);
      const result = toJsTimestamp(epochDate);

      expect(result).toBe(0);
    });

    it('should handle current date', () => {
      const now = new Date();
      const result = toJsTimestamp(now);

      expect(result).toBe(now.getTime());
    });
  });

  describe('convertUnixTimestamp', () => {
    it('should convert JavaScript timestamp to Unix timestamp', () => {
      const jsTimestamp = 1704067200000;
      const expectedUnix = 1704067200;
      const result = convertUnixTimestamp(jsTimestamp);

      expect(result).toBe(expectedUnix);
    });

    it('should truncate milliseconds', () => {
      const jsTimestamp = 1704067200999; // 999ms should be truncated
      const expectedUnix = 1704067200;
      const result = convertUnixTimestamp(jsTimestamp);

      expect(result).toBe(expectedUnix);
    });

    it('should handle zero', () => {
      expect(convertUnixTimestamp(0)).toBe(0);
    });

    it('should handle small values', () => {
      expect(convertUnixTimestamp(1000)).toBe(1);
      expect(convertUnixTimestamp(500)).toBe(0);
    });
  });

  describe('toUnixTimestamp', () => {
    it('should convert Date to Unix timestamp (seconds)', () => {
      const date = new Date('2024-01-01T00:00:00Z');
      const result = toUnixTimestamp(date);

      expect(typeof result).toBe('number');
      expect(result).toBe(Math.trunc(date.getTime() / 1000));
    });

    it('should return seconds since Unix epoch', () => {
      const epochDate = new Date(0);
      const result = toUnixTimestamp(epochDate);

      expect(result).toBe(0);
    });

    it('should truncate milliseconds', () => {
      const dateWithMs = new Date('2024-01-01T00:00:00.999Z');
      const dateWithoutMs = new Date('2024-01-01T00:00:00.000Z');

      expect(toUnixTimestamp(dateWithMs)).toBe(toUnixTimestamp(dateWithoutMs));
    });
  });

  describe('roundtrip conversions', () => {
    it('should roundtrip from Date through Unix timestamp back to Date', () => {
      const originalDate = new Date('2024-06-15T12:30:00Z');
      const unixTimestamp = toUnixTimestamp(originalDate);
      const recoveredDate = fromUnixTimestamp(unixTimestamp);

      // Milliseconds are lost in Unix timestamp conversion
      expect(recoveredDate.getUTCFullYear()).toBe(originalDate.getUTCFullYear());
      expect(recoveredDate.getUTCMonth()).toBe(originalDate.getUTCMonth());
      expect(recoveredDate.getUTCDate()).toBe(originalDate.getUTCDate());
      expect(recoveredDate.getUTCHours()).toBe(originalDate.getUTCHours());
      expect(recoveredDate.getUTCMinutes()).toBe(originalDate.getUTCMinutes());
      expect(recoveredDate.getUTCSeconds()).toBe(originalDate.getUTCSeconds());
    });

    it('should roundtrip from Date through JS timestamp back to Date', () => {
      const originalDate = new Date('2024-06-15T12:30:45.123Z');
      const jsTimestamp = toJsTimestamp(originalDate);
      const recoveredDate = fromJsTimestamp(jsTimestamp);

      expect(recoveredDate.getTime()).toBe(originalDate.getTime());
    });
  });
});
