import base64

import requests
from requests import auth
from requests.auth import HTTPBasicAuth

from db import session_scope
from db.sensors import Sensors as SensorsDB
from lib.sensors import InvalidDataType, SensorBase
from lib.units import to_g

def _calc_fract_remaining(sensor, data, config, logger, *args, **kwargs):
        logger.debug("*****************************************************************************************************")
        logger.debug("*********** CALCULATING FRACTION OF LIQUID REMAINING ************************************************")
        logger.debug("*****************************************************************************************************")

        empty_keg_weight_g = 0
        if sensor.meta:
            empty_keg_weight = sensor.meta.get("empty_keg_weight", 0)
            logger.debug(f"(meta) empty keg weight: {empty_keg_weight}")
            empty_keg_weight_unit = sensor.meta.get("empty_keg_weight_unit", "g")
            logger.debug(f"(meta) empty keg weight unit: {empty_keg_weight_unit}")

            empty_keg_weight_g = empty_keg_weight
            if empty_keg_weight_unit != "g":
                logger.debug("converting empty keg weight to grams")
                empty_keg_weight_g = to_g(empty_keg_weight, empty_keg_weight_unit)
                logger.debug(f"empty keg weight in grams: {empty_keg_weight_g}")
        
        
        unit = data.get("weight_raw_unit", "kg")
        logger.debug(f"(OPK Service) weight unit: {unit}")
        full_weight = data.get("full_weight")
        logger.debug(f"(OPK Service) full weight: {full_weight}")
        weight = data.get("weight")
        logger.debug(f"(OPK Service) weight: {weight}")

        full_weight_g = full_weight
        weight_g = weight
        if unit != "g":
            logger.debug("convirting full weight to grams")
            full_weight_g = to_g(full_weight, unit)
            logger.debug(f"full weight in grams: {full_weight_g}")
            logger.debug("convirting weight to grams")
            weight_g = to_g(weight, unit)
            logger.debug(f"weight in grams: {weight_g}")

        if weight_g <= empty_keg_weight_g:
            logger.debug(f"Weight in grams ({weight_g}) is less than empty keg weight in grams ({empty_keg_weight_g})... returning 0")
            return 0
        
        # remove the empty keg weight to get teh real percentage
        logger.debug(f"Recalculating weights removing empty keg weight for more precise fraction of actual liquid remaining")
        liquid_full_weight_g = (float(full_weight_g) - float(empty_keg_weight_g))
        logger.debug(f"liquid full weight in g: {liquid_full_weight_g}")
        liquid_weight_g = (float(weight_g) - float(empty_keg_weight_g))
        logger.debug(f"liquid weight in g: {liquid_weight_g}")
        
        if liquid_weight_g <= 0:
            logger.debug(f"Liquid weight in grams ({liquid_weight_g}) is less than 0, returning 0")
            return 0
        
        
        frac =  (liquid_weight_g / liquid_full_weight_g)
        if frac > 1:
            return 1
        logger.debug(f"Fraction remaining: {frac}")
        return frac

def _calc_percent_remaining(sensor, data, config, logger, *args, **kwargs):    
        return _calc_fract_remaining(sensor, data, config, logger, *args, **kwargs) * 100

def _calc_total_vol_remaining(sensor, data, config, logger, *args, **kwargs):
    if not sensor.meta:
        return 0
    
    max_vol = sensor.meta.get("max_keg_volume")
    if not max_vol:
        return 0
    
    return max_vol * _calc_fract_remaining(sensor, data, config, logger, *args, **kwargs)

def _get_display_volume_unit(sensor, data, config, logger, *args, **kwargs):
    def_display_unit = config.get("sensors.preferred_vol_unit")
    if not sensor.meta:
        return def_display_unit
    
    return sensor.meta.get("max_keg_volume_unit", def_display_unit)

def _get_firmware_version(*args, **kwargs):
    return "Unknown"

KEYMAP = {
    "percent_beer_remaining": _calc_percent_remaining,
    "total_beer_remaining": _calc_total_vol_remaining,
    "beer_remaining_unit": _get_display_volume_unit,
    "firmware_version": _get_firmware_version
}

class OpenPlaatoKeg(SensorBase):
    def supports_discovery(self):
        return True
    
    def get(self, key, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = self._get(f"kegs/{device_id}")
        fn = KEYMAP.get(key, None)

        if not fn:
            return None
        return fn(sensor, data, self.config, self.logger)

    def get_all(self, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = self._get(f"kegs/{device_id}")

        return {
            "percentRemaining": _calc_percent_remaining(sensor, data, self.config, self.logger),
            "totalVolumeRemaining": _calc_total_vol_remaining(sensor, data, self.config, self.logger),
            "displayVolumeUnit": _get_display_volume_unit(sensor, data, self.config, self.logger),
            "firmwareVersion": _get_firmware_version(sensor, data, self.config, self.logger)
        }
    
    def discover(self):
        devices = self._get("kegs")

        return [{"id": dev["id"], "name": dev["name"]} for dev in devices]
    

    def _get(self, path, params=None):
        kwargs = {}
        base_url = self.config.get("sensors.open_plaato_keg.base_url") 
        insecure = self.config.get("sensors.open_plaato_keg.insecure")

        if insecure:
            kwargs["verify"] = False 
        
        url = f"{base_url}/api/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        
        resp = requests.get(url, params=params, **kwargs)
        self.logger.debug("GET response code: %s", resp.status_code)
        
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j
