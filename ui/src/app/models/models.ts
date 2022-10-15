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

export class EditableBase {
  isEditing: boolean;
  editValues: any;
  #fields: string[];
  #transformFns: any;

  constructor(fields: string[], from?: any, transformFns?: any) {
    if(!isNilOrEmpty(from)) {
      this.from(from);
    }
    
    this.#transformFns = isNilOrEmpty(transformFns) ? {} : transformFns;
    this.isEditing = false;
    this.editValues = {}
    this.#fields = fields;
  }

  from(from: any) {
    Object.assign(this, from);
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

  constructor(from?: any) {
    super(["name", "description"], from);
  }
}

export class Tap extends EditableBase {
  id!: string;
  description!: string;
  tapNumber!: number;
  locationId!: string;
  location: Location | undefined;
  beerId!: string;
  beer: Beer | undefined;
  beverageId!: string;
  beverage: Beverage | undefined;
  sensorId!: string;
  sensor: Sensor | undefined;
  coldBrew: ColdBrew | undefined;
  namePrefix!: string;
  nameSuffix!: string;

  get tapType(): string | undefined {
    if (!isNilOrEmpty(this.beerId))
      return "beer";

    if (!isNilOrEmpty(this.beverageId))
      return "beverage";
    return undefined;
  }

  constructor(from?: any) {
    super(["description", "tapNumber", "locationId", "beerId", "sensorId", "beverageId", "namePrefix", "nameSuffix"], from);
  }

  getDisplayName(name?: string) : string | undefined {
    if (isNilOrEmpty(name)) {
      if (this.beer) {
        name = this.beer.getName();
      }

      if (this.coldBrew) {
        name = this.coldBrew.name;
      }

      if (this.beverage) {
        name = this.beverage.name;
      }

      if (isNilOrEmpty(name)) {
        return name;
      }
    }

    if (!isNilOrEmpty(this.namePrefix)) {
      name = this.namePrefix + name;
    }

    if (!isNilOrEmpty(this.nameSuffix)) {
      name = name + this.nameSuffix;
    }
    
    return name;
  }
}

export class ImageTransitionalBase extends EditableBase {
  emptyImgUrl!: string;
  imageTransitions: ImageTransition[] | undefined;
  imageTransitionsEnabled!: boolean;
  imgUrl!: string;

  constructor(fields: string[], from?: any, transformFns?: any) {
    super(fields, from, transformFns);
    if(!isNilOrEmpty(from) && !isNilOrEmpty(from.imageTransitions)) {
      this.imageTransitions = [];
      for(let i of from.imageTransitions) {
        this.imageTransitions.push(new ImageTransition(i));
      }
      this.imageTransitions = _.orderBy(this.imageTransitions, ["changePercent"], ["desc"]);
    }
  }

  override enableEditing(): void {
    super.enableEditing();

    if(this.imageTransitions) {
      for(let i of this.imageTransitions) {
        i.enableEditing();
      }
    }
  }

  override disableEditing(): void {
    super.disableEditing();

    if(this.imageTransitions) {
      for(let i of this.imageTransitions) {
        i.disableEditing();
      }
    }
  }

  getImgUrl() {
    return this.imgUrl;
  }
}

export class Beer extends ImageTransitionalBase {
  id!: string;
  description!: string;
  name!: string;
  brewery!: string;
  externalBrewingTool!: string;
  externalBrewingToolMeta!: any;
  style!: number;
  abv!: string;
  ibu!: number;
  kegDate!: number;
  brewDate!: number;
  srm!: number;
  untappdId!: string;
  taps: Tap[] | undefined;

  constructor(from?: any) {
    super(["name", "description", "externalBrewingTool", "externalBrewingToolMeta", "style", "abv", "imgUrl", "ibu", "kegDate", "brewDate", "srm", "untappdId", "emptyImgUrl", "imageTransitions", "imageTransitionsEnabled"], from, beerTransformFns);
    if(isNilOrEmpty(this.externalBrewingToolMeta)) {
      this.externalBrewingToolMeta = {}
    }
    
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

  override getImgUrl() {
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

  constructor(from?: any) {
    super(["name", "locationId", "sensorType", "meta"], from);
    if(isNilOrEmpty(this.meta)){
      this.meta = {}
    }
  }
}

export class UserInfo extends EditableBase {
  id!: string;
  email!: string;
  firstName!: string;
  lastName!: string;
  profilePic!: string;
  passwordEnabled!: boolean;

  constructor(from?: any) {
    super(["email", "firstName", "lastName", "profilePic"], from);
  }
}

export class TapRefreshSettings {
  baseSec: number;
  variable: number;

  constructor(from?: any) {
    this.baseSec = 300;
    this.variable = 150;

    if(!isNilOrEmpty(from)) {
      Object.assign(this, from);
    }
  }
}

export class TapSettings {
  refresh: TapRefreshSettings;

  constructor(from?: any) {
    this.refresh = new TapRefreshSettings();

    if(!isNilOrEmpty(from)) {
      Object.assign(this, from);
    }
  }
}

export class BeverageSettings {
  defaultType!: string;
  supportedTypes: string[];

  constructor(from?: any) {
    this.supportedTypes = [];

    if(!isNilOrEmpty(from)) {
      Object.assign(this, from);
    }
  }
}

export class Settings {
  googleSSOEnabled: boolean;
  taps: TapSettings;
  beverages: BeverageSettings;

  constructor(from?: any) {
    this.googleSSOEnabled = false;
    this.taps = new TapSettings;
    this.beverages = new BeverageSettings;


    if(!isNilOrEmpty(from)) {
      Object.assign(this, from);
    }
  }
}

export class Beverage extends ImageTransitionalBase {
  id!: string;
  description!: string;
  name!: string;
  brewery!: string;
  breweryLink!: string;
  type!: string;
  flavor!: string;
  kegDate!: number;
  brewDate!: number;
  meta!: any;
  taps: Tap[] | undefined;

  constructor(from?: any) {
    super(["name", "description", "brewery", "breweryLink", "type", "flavor", "imgUrl", "kegDate", "brewDate", "meta"], from);
    if(isNilOrEmpty(this.meta)){
      this.meta = {};
    }
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

  #getDateDisplay(d: number) : string | undefined {
    return isNilOrEmpty(d) ? undefined : formatDate(fromUnixTimestamp(d))
  }

  getBrewDateDisplay() : string | undefined {
    return this.#getDateDisplay(this.brewDate);
  }

  getKegDateDisplay() : string | undefined {
    return this.#getDateDisplay(this.kegDate);
  }
}

export class ColdBrew extends Beverage {
  roastery: string | undefined;
  roasteryLink: string | undefined;

  constructor(from?: any) {
    super(from);

    this.roastery = this.#getMeta("roastery");
    this.roasteryLink = this.#getMeta("roasteryLink");
  }

  #getMeta(path: string): any {
    if (!isNilOrEmpty(this.meta))
      return _.get(this.meta, path);

    return undefined;
  }
}

export class ImageTransition extends EditableBase {
  id!: string;
  beerId!: string;
  beverageId!: string;
  imgUrl!: string;
  changePercent!: number;

  constructor(from?: any) {
    super(["imgUrl", "changePercent"], from);
  }
}