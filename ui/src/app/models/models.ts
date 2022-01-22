// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */
// this check reports that some of these types shadow their own definitions
/* eslint-disable no-shadow */

import * as _ from 'lodash';
import { deepEqual, isObject } from '../utils/helpers';

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

  constructor(fields: string[]) {
      this.isEditing = false;
      this.editValues = {}
      this.#fields = fields;
  }

  enableEditing(): void{
      this.isEditing = true;
      this.editValues = _.cloneDeep(this);
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
            const v2 = this.editValues[key];
            if (isObject(v1) && isObject(v2)) {
              if (!deepEqual(v1, v2)) {
                dataChanges[key] = this.editValues[key]
              }
            } else {
              if(v1 !== v2){
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

export class Tap {
  id!: string;
  description!: string;
  tapNumber!: number;
  locationId!: string;
  tapType!: string;
  beerId!: string;
  coldBrewId!: string;
  sensorId!: string;
}

export class Beer {
  id!: string;
  description!: string;
  name!: string;
  locationId!: string;
  externalBrewingTool!: string;
  externalBrewingToolMeta!: Object;
  style!: number;
  abv!: string;
  imgUrl!: string;
  ibu!: number;
  kegDate!: string;
  brewDate!: string;
  srm!: number;
}

export class Sensor extends EditableBase {
  id!: string;
  name!: string;
  sensorType!: string;
  locationId!: string;
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