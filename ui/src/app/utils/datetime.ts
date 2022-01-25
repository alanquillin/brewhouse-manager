import * as _ from 'lodash';

export function formatDate(d: Date): string | undefined {
    if(_.isNil(d)) {
        return d;
    }

  var year = d.getFullYear();
  var month = d.getMonth();
  var day = d.getDay()

  return `${month}/${day}/${year}`;
}


export function fromUnixTimestamp(ts: number): Date {
  return fromJsTimestamp(ts * 1000);
}

export function fromJsTimestamp(ts: number): Date {
  return new Date(ts);
}

export function toUnixTimestamp(d: Date): number {
  return toJsTimestamp(d) / 1000;
}

export function toJsTimestamp(d: Date): number {
  return d.getTime()
}