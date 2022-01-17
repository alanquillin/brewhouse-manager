from resources import BaseResource, ResourceMixinBase, NotFoundError, ClientError
from db import session_scope
from db.sensors import Sensors as SensorsDB, _PKEY as sensors_pk
from lib.sensors import get_sensor_lib, InvalidDataType

class Sensors(BaseResource, ResourceMixinBase):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            if location:
                location_id = self.get_location_id(location, db_session)
                sensors = SensorsDB.get_by_location(db_session, location_id)
            else:
                sensors = SensorsDB.query(db_session)
            return [self.transform_response(t.to_dict()) for t in sensors]


class Sensor(BaseResource, ResourceMixinBase):
    def get(self, sensor_id, location=None):
        with session_scope(self.config) as db_session:
            sensor = None
            if location:
                query = {
                    "location_id": self.get_location_id(location, db_session),
                    sensors_pk: sensor_id
                }
                resp = SensorsDB.query(db_session, **query)
                if resp:
                    sensor = resp[0]
            else:    
                sensor = SensorsDB.get_by_pkey(db_session, sensor_id)
            
            if not sensor:
                raise NotFoundError()

            return self.transform_response(sensor.to_dict())

class SensorData(BaseResource, ResourceMixinBase):
    def get(self, sensor_id, data_type, location=None):
        with session_scope(self.config) as db_session:
            sensor = None
            if location:
                query = {
                    "location_id": self.get_location_id(location, db_session),
                    sensors_pk: sensor_id
                }
                resp = SensorsDB.query(db_session, **query)
                if resp:
                    sensor = resp[0]
            else:    
                sensor = SensorsDB.get_by_pkey(db_session, sensor_id)
            
            if not sensor:
                raise NotFoundError()
                
            sensor_lib = get_sensor_lib(sensor.sensor_type)
            try:
                return sensor_lib.get(data_type, sensor=sensor)
            except InvalidDataType as ex:
                raise ClientError(user_msg=ex.message)