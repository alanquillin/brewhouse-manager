import * as _ from 'lodash';

export function formatDate(d: Date): string | undefined {
    if(_.isNil(d)) {
        return d;
    }

  return d.toLocaleDateString();
}


export function fromUnixTimestamp(ts: number): Date {
  return fromJsTimestamp(ts * 1000);
}

export function fromJsTimestamp(ts: number): Date {
  return new Date(ts);
}

export function toUnixTimestamp(d: Date): number {
  return convertUnixTimestamp( toJsTimestamp(d));
}

export function convertUnixTimestamp(d: number): number {
  return Math.trunc(d / 1000);
}

export function toJsTimestamp(d: Date): number {
  return d.getTime()
}