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
  batchId!: string;
  batch: Batch | undefined;
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
    super(["description", "tapNumber", "locationId", "beerId", "sensorId", "beverageId", "namePrefix", "nameSuffix", "batchId"], from);
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

  override from(from: any) {
    if(_.isNil(from.batchId)){
      _.unset(this, 'batchId');
      this.batch = undefined;
    }
    if(_.isNil(from.beerId)){
      _.unset(this, 'beerId');
      this.beer = undefined
    }
    if(_.isNil(from.beverageId)){
      _.unset(this, 'beverageId');
      this.beverage = undefined;
    }
    super.from(from);
  }
}

export class ImageTransitionalBase extends EditableBase {
  emptyImgUrl!: string;
  imageTransitions: ImageTransition[] | undefined;
  imageTransitionsEnabled!: boolean;
  imgUrl!: string;

  constructor(fields: string[], from?: any, transformFns?: any) {
    fields.push("emptyImgUrl");
    fields.push("imageTransitions");
    fields.push("imageTransitionsEnabled");
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

  getImgUrl(batch?: Batch|undefined) {
    if (batch !== undefined && !isNilOrEmpty(batch.imgUrl)){ 
      return batch.imgUrl
    }
    
    return this.imgUrl;
  }
}

export class ExtToolBase extends ImageTransitionalBase {
  externalBrewingTool!: string;
  externalBrewingToolMeta!: any;

  constructor(fields: string[], from?: any, transformFns?: any) {
    fields.push("externalBrewingTool");
    fields.push("externalBrewingToolMeta");

    super(fields, from, transformFns);
  }

  getVal(key: string, batch?: Batch|undefined, transformFn?: Function, brewToolTransformFn?: any): any{
    if (batch !== undefined){
      var bv = batch.getVal(key, undefined, transformFn, brewToolTransformFn);
      if(!isNilOrEmpty(bv)){
        return bv;
      }
    }
    
    var v = _.get(this, key)
    if(isNilOrEmpty(v)) {
      v = this.getExtToolVal(key, brewToolTransformFn);
    } else {
      if (!_.isNil(transformFn)) {
        v = transformFn(v);
      }
    }

    return v;
  }

  getExtToolVal(key: string, brewToolTransformFn?: any) : any {
    var v = null;
    if(!_.isEmpty(this.externalBrewingTool) && !_.isEmpty(this.externalBrewingToolMeta)) {
      if(this.externalBrewingTool === "brewfather") {
        v = _.get(this.externalBrewingToolMeta, `details.${key}`);
      }
      if(!_.isNil(v) && _.has(brewToolTransformFn, this.externalBrewingTool)) {
        v = brewToolTransformFn[this.externalBrewingTool](v);
      }
    }
    return v;
  }

  getName(batch?: Batch|undefined) {
    return this.getVal("name", batch);
  }

  getAbv(batch?: Batch|undefined) {
    return this.getVal("abv", batch);
  }

  getIbu(batch?: Batch|undefined) {
    return this.getVal("ibu", batch);
  }

  getSrm(batch?: Batch|undefined) {
    return this.getVal("srm", batch);
  }
}

export class Batch extends ExtToolBase {
  id!: string;
  beerId!: string;
  beer: Beer | undefined;
  beverageId!: string;
  beverage: Beverage | undefined;
  abv!: string;
  ibu!: number;
  srm!: number;
  kegDate!: number;
  brewDate!: number;
  archivedOn!: number;
  taps!: Tap[] | undefined;
  batchNumber!: string;
  name!: string;
  locationIds!: string[];
  locations: Location[] | undefined;

  constructor(from?: any) {
    super(["name", "beerId", "beverageId", "locationIds", "abv", "ibu", "srm", "kegDate", "brewDate", "archivedOn", "batchNumber", "imgUrl"], from, beerTransformFns);
    if(isNilOrEmpty(this.externalBrewingToolMeta)) {
      this.externalBrewingToolMeta = {}
    }
  }

  override cloneValuesForEditing() {
    super.cloneValuesForEditing();
    this.editValues["brewDateObj"] = isNilOrEmpty(this.brewDate) ? undefined : fromUnixTimestamp(this.brewDate)
    this.editValues["kegDateObj"] = isNilOrEmpty(this.kegDate) ? undefined : fromUnixTimestamp(this.kegDate)
    this.editValues["archivedOnObj"] = isNilOrEmpty(this.archivedOn) ? undefined : fromUnixTimestamp(this.archivedOn)
  }

  override get changes() {
    this.editValues["brewDate"] = isNilOrEmpty(this.editValues["brewDateObj"]) ? undefined : toUnixTimestamp(this.editValues["brewDateObj"]);
    this.editValues["kegDate"] = isNilOrEmpty(this.editValues["kegDateObj"]) ? undefined : toUnixTimestamp(this.editValues["kegDateObj"]);
    this.editValues["archivedOn"] = isNilOrEmpty(this.editValues["archivedOnObj"]) ? undefined : toUnixTimestamp(this.editValues["archivedOnObj"]);
        
    var changes = super.changes;

    return changes;
  }

  getBatchNumber() {
    return this.getVal("batchNumber")
  }

  getKegDate() {
    return this.getVal("kegDate", undefined, (v: any) => {return this.getDateDisplay(v);}, {"brewfather": (v: any) => {return this.getDateDisplay(v);}});
  }
  
  getBrewDate() {
    return this.getVal("brewDate", undefined, (v: any) => {return this.getDateDisplay(v);}, {"brewfather": (v: any) => {return this.getDateDisplay(v);}});
  }

  getDateDisplay(d: any) : string | undefined {
    if(isNilOrEmpty(d) || !_.isNumber(d)) {
      return undefined
    }
    return formatDate(d < 9999999999 ? fromUnixTimestamp(d) : fromJsTimestamp(d));
  }
}

export class Beer extends ExtToolBase {
  id!: string;
  description!: string;
  name!: string;
  brewery!: string;
  style!: number;
  abv!: string;
  ibu!: number;
  srm!: number;
  untappdId!: string;

  constructor(from?: any) {
    super(["name", "description", "style", "abv", "imgUrl", "ibu", "srm", "untappdId"], from, beerTransformFns);
    if(isNilOrEmpty(this.externalBrewingToolMeta)) {
      this.externalBrewingToolMeta = {}
    }
  }

  getDescription(batch?: Batch|undefined) {
    return this.getVal("description", batch);
  }
  getStyle(batch?: Batch|undefined) {
    return this.getVal("style", batch);
  }

  override getImgUrl(batch?: Batch|undefined) {
    return this.getVal("imgUrl", batch);
  }
}

export class Sensor extends EditableBase {
  id!: string;
  name!: string;
  sensorType!: string;
  locationId!: string;
  location: Location | undefined;
  meta!: any;
  tap!: Tap;

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
  admin!: boolean;
  apiKey!: string;
  locations: Location[] | undefined;

  constructor(from?: any) {
    super(["email", "firstName", "lastName", "profilePic", "admin"], from);
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

export class DashboardSettings {
  refreshSec!: number;

  constructor(from?: any) {
    this.refreshSec = 15;

    if(!isNilOrEmpty(from)) {
      Object.assign(this, from);
    }
  }
}

export class Settings {
  googleSSOEnabled: boolean;
  taps: TapSettings;
  beverages: BeverageSettings;
  dashboard: DashboardSettings;

  constructor(from?: any) {
    this.googleSSOEnabled = false;
    this.taps = new TapSettings;
    this.beverages = new BeverageSettings;
    this.dashboard = new DashboardSettings;

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
  meta!: any;
  taps: Tap[] | undefined;

  constructor(from?: any) {
    super(["name", "description", "brewery", "breweryLink", "type", "flavor", "imgUrl", "meta"], from);
    if(isNilOrEmpty(this.meta)){
      this.meta = {};
    }
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

export class Dashboard {
  location!: Location;
  taps!: Tap[];
  locations!: Location[];
}

export class SensorData {
  percentRemaining!: number;
  totalVolumeRemaining!: number;
  displayVolumeUnit!: string;
  firmwareVersion!: string
}

export class SensorDiscoveryData {
  id!: string;
  name!: string;
  model!: string;
  portNum!: number;
  token!: string;
}

export class PlaatoKegDevice extends EditableBase {
  id!: string;  // Device ID
  name?: string;
  connected!: boolean;
  lastUpdatedOn?: Date;

  // Telemetry data
  percentOfBeerLeft?: number;
  amountLeft?: number;
  beerLeftUnit?: string;
  kegTemperature?: number;
  temperatureUnit?: string;
  lastPour?: string;
  isPouring?: boolean;

  // Beer info
  og?: number;
  fg?: number;
  calculatedAbv?: number;
  beerStyle?: string;

  // Configuration
  emptyKegWeight?: number;
  maxKegVolume?: number;
  unit?: string;
  measureUnit?: string;
  mode?: string;  // 'beer' or 'co2'
  unitType?: string;  // 'metric' or 'us'
  unitMode?: string;  // 'weight' or 'volume'

  // Device health
  wifiSignalStrength?: number;
  firmwareVersion?: string;
  chipTemperature?: number;
  leakDetection?: boolean;

  constructor(from?: any) {
    super(['name'], from);
  }
}

export class PlaatoDeviceResponse {
  status!: string
  msg!: string
}