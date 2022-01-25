// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */
// this check reports that some of these types shadow their own definitions
/* eslint-disable no-shadow */

import * as _ from 'lodash';
import { deepEqual, isObject } from '../utils/helpers';
import { fromJsTimestamp, formatDate, fromUnixTimestamp, toUnixTimestamp } from '../utils/datetime';

import { isNilOrEmpty } from '../utils/helpers'

export const beerTransformFns = {
  abv: (v: any) => {return isNilOrEmpty(v) ? undefined : _.toNumber(v)},
  ibu: (v: any) => {return isNilOrEmpty(v) ? undefined : _.toNumber(v)},
  srm: (v: any) => {return isNilOrEmpty(v) ? undefined : _.toNumber(v)},
  externalBrewingToolMeta: (v: any) => {return _.isNil(v) ? v : _.cloneDeep(v)},
  externalBrewingTool: (v: any) => {return isNilOrEmpty(v) || v === "-1" ? undefined : v},
  brewDate: (v: any) => {return isNilOrEmpty(v) ? undefined : _.isDate(v) ? toUnixTimestamp(v) : _.toNumber(v);},
  kegDate: (v: any) => {return isNilOrEmpty(v) ? undefined : _.isDate(v) ? toUnixTimestamp(v) : _.toNumber(v);}
}

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

export class EditableBase {
  isEditing: boolean;
  editValues: any;
  #fields: string[];
  #transformFns: any;

  constructor(fields: string[], transformFns?: any) {
    this.#transformFns = isNilOrEmpty(transformFns) ? {} : transformFns;
    this.isEditing = false;
    this.editValues = {}
    this.#fields = fields;
  }

  cloneValuesForEditing() {
    this.editValues = _.cloneDeep(this);
  }

  enableEditing(): void{
    this.isEditing = true;
    this.cloneValuesForEditing();
  }

  disableEditing(): void {
    this.isEditing = false;
    this.editValues = {};
  }

  get changes(): any {
    var dataChanges: any = {}

    if(this.isEditing) {
      _.forEach(this.#fields, (key) => {
        const v1 = _.get(this, key);
        var v2 = _.get(this.editValues, key);
        const transformFn = _.get(this.#transformFns, key)
        if (!_.isNil(transformFn)) {
          v2 = transformFn(v2);
        }
        if (isObject(v1) && isObject(v2)) {
          if (!deepEqual(v1, v2)) {
            dataChanges[key] = this.editValues[key]
          }
        } else {
          if(v1 !== v2 && !(isNilOrEmpty(v1) && isNilOrEmpty(v2))) {
            dataChanges[key] = this.editValues[key]
          }
        }
      });
    }

    return dataChanges;
  }

  get hasChanges(): boolean {
    return !this.isEditing ? false : !_.isEmpty(this.changes);
  }
}

export class Location extends EditableBase {
  id!: string;
  description!: string;
  name!: string;

  constructor() {
    super(["name", "description"]);
  }
}

export class Tap extends EditableBase {
  id!: string;
  description!: string;
  tapNumber!: number;
  locationId!: string;
  location: Location | undefined;
  tapType!: string;
  beerId!: string;
  beer: Beer | undefined;
  sensorId!: string;
  sensor: Sensor | undefined;

  constructor() {
    super(["description", "tapNumber", "locationId", "tapType", "beerId", "sensorId"]);
  }
}

export class Beer extends EditableBase {
  id!: string;
  description!: string;
  name!: string;
  externalBrewingTool!: string;
  externalBrewingToolMeta!: any;
  style!: number;
  abv!: string;
  imgUrl!: string;
  ibu!: number;
  kegDate!: number;
  brewDate!: number;
  srm!: number;

  constructor() {
    super(["name", "description", "externalBrewingTool", "externalBrewingToolMeta", "style", "abv", "imgUrl", "ibu", "kegDate", "brewDate", "srm"], beerTransformFns);
    this.externalBrewingToolMeta = {}
  }

  #getVal(key: string, transformFn?: Function, brewToolTransformFn?: any): any{
    var v = _.get(this, key)
    if(isNilOrEmpty(v)) {
      if(!_.isEmpty(this.externalBrewingTool) && !_.isEmpty(this.externalBrewingToolMeta)) {
        if(this.externalBrewingTool === "brewfather") {
          v = _.get(this.externalBrewingToolMeta, `details.${key}`);
        }
        if(!_.isNil(v) && _.has(brewToolTransformFn, this.externalBrewingTool)) {
          v = brewToolTransformFn[this.externalBrewingTool](v);
        }
      }
    } else {
      if (!_.isNil(transformFn)) {
        v = transformFn(v);
      }
    }

    return v;
  }

  override cloneValuesForEditing() {
    super.cloneValuesForEditing();
    this.editValues["brewDateObj"] = isNilOrEmpty(this.brewDate) ? undefined : fromUnixTimestamp(this.brewDate)
    this.editValues["kegDateObj"] = isNilOrEmpty(this.kegDate) ? undefined : fromUnixTimestamp(this.kegDate)
  }

  override get changes() {
    this.editValues["brewDate"] = isNilOrEmpty(this.editValues["brewDateObj"]) ? undefined : toUnixTimestamp(this.editValues["brewDateObj"]);
    this.editValues["kegDate"] = isNilOrEmpty(this.editValues["kegDateObj"]) ? undefined : toUnixTimestamp(this.editValues["kegDateObj"]);
        
    var changes = super.changes;

    return changes;
  }

  getName() {
    return this.#getVal("name");
  }

  getDescription() {
    return this.#getVal("description");
  }
  getStyle() {
    return this.#getVal("style");
  }

  getAbv() {
    return this.#getVal("abv");
  }

  getImgUrl() {
    return this.#getVal("imgUrl");
  }

  getIbu() {
    return this.#getVal("ibu");
  }

  getKegDate() {
    return this.#getVal("kegDate", (v: any) => {return formatDate(fromUnixTimestamp(v));}, {"brewfather": (v: any) => {return formatDate(fromJsTimestamp(v));}});
  }
  
  getBrewDate() {
    return this.#getVal("brewDate", (v: any) => {return formatDate(fromUnixTimestamp(v));}, {"brewfather": (v: any) => {return formatDate(fromJsTimestamp(v));}});
  }

  getSrm() {
    return this.#getVal("srm");
  }
}

export class Sensor extends EditableBase {
  id!: string;
  name!: string;
  sensorType!: string;
  locationId!: string;
  location: Location | undefined;
  meta!: any;

  constructor() {
    super(["name", "locationId", "sensorType", "meta"]);
    this.meta = {}
  }
}

export class UserInfo {
  id!: string;
  email!: string;
  firstName!: string;
  lastName!: string;
  profilePic!: string;
  passwordEnabled!: boolean;
}