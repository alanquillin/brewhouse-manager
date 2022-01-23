import { Tap, Beer, Sensor } from './../models/models';

export class TapDetails extends Tap {
  isEmpty!: boolean;
  isLoading!: boolean;
  override sensor!: SensorData;
}

export class SensorData extends Sensor {
  percentBeerRemaining!: number;
}