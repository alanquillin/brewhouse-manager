from typing import List, Optional
from pydantic import Field
from datetime import datetime

from schemas.base import CamelCaseModel

class PlaatoKegBase(CamelCaseModel):
    id: str
    lastPourString: Optional[str] = None
    percentOfBeerLeft: Optional[float] = None
    isPouring: Optional[bool] = None
    amountLeft: Optional[float] = None
    temperatureOffset: Optional[float] = None
    kegTemperature: Optional[float] = None
    lastPour: Optional[float] = None
    emptyKegWeight: Optional[float] = None
    og: Optional[float] = None
    fg: Optional[float] = None
    kegTemperatureString: Optional[str] = None
    beerLeftUnit: Optional[str] = None
    maxKegVolume: Optional[float] = None
    temperatureUnit: Optional[str] = None
    wifiSignalStrength: Optional[int] = None
    volumeUnit: Optional[str] = None
    leakDetection: Optional[bool] = None
    minTemperature: Optional[float] = None
    maxTemperature: Optional[float] = None
    chipTemperatureString: Optional[str] = None
    firmwareVersion: Optional[str] = None
    updatedOn: datetime
    beerStyle: Optional[str] = None
    unitMode: str # Either weight or volume
    unitType: str # Either us or metric
    calculatedAbv: Optional[float] = None
    connected: bool
    mode: str
    name: Optional[str] = None


class PlaatoKegCreate(CamelCaseModel):
    id: str
    name: str


class PlaatoKegUpdate(CamelCaseModel):
    name: str