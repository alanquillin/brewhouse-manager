// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */
// this check reports that some of these types shadow their own definitions
/* eslint-disable no-shadow */

export class DataError extends Error {
  statusCode!: number;

  constructor(message?: string, statusCode?: any | undefined){
    super(message);
    if (statusCode !== undefined){
      this.statusCode = statusCode;
    }
  }
}
export class Location {
  id!: string;
  description!: string;
  name!: string;
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

export class Sensor {
  id!: string;
  name!: string;
  locationId!: string;
  meta!: Object;
}