import * as _ from "lodash";

export function deepEqual(object1: any, object2: any): boolean {
    const keys1 = Object.keys(object1);
    const keys2 = Object.keys(object2);
    if (keys1.length !== keys2.length) {
      return false;
    }
    for (const key of keys1) {
      const val1 = object1[key];
      const val2 = object2[key];
      const areObjects = isObject(val1) && isObject(val2);
      if (
        areObjects && !deepEqual(val1, val2) ||
        !areObjects && val1 !== val2
      ) {
        return false;
      }
    }
    return true;
  }

  export function isObject(object: any): boolean {
    return object != null && typeof object === 'object';
  }

  export function isNilOrEmpty(val: any): boolean {
    if (_.isNil(val)){
      return true;
    }

    if (_.isBoolean(val)){
      return false;
    }

    if (_.isDate(val)) {
      return _.isEqual(new Date(), val);
    }

    if(_.isNumber(val)) {
      return _.isNaN(val);
    }

    return _.isEmpty(val);
  }