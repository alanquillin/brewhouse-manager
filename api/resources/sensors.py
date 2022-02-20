from flask_login import login_required

from db import session_scope
from db.sensors import _PKEY as sensors_pk
from db.sensors import Sensors as SensorsDB
from lib.sensors import InvalidDataType, get_sensor_lib
from lib.sensors import get_types as get_sensor_types
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase
from resources.locations import LocationsResourceMixin


class SensorResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(sensor):
        data = sensor.to_dict()

        if sensor.location:
            data["location"] = LocationsResourceMixin.transform_response(sensor.location)

        return ResourceMixinBase.transform_response(data)


class Sensors(BaseResource, SensorResourceMixin):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            if location:
                location_id = self.get_location_id(location, db_session)
                sensors = SensorsDB.get_by_location(db_session, location_id)
            else:
                sensors = SensorsDB.query(db_session)
            return [self.transform_response(t) for t in sensors]

    @login_required
    def post(self, location=None):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()
            if not "location_id" in data and location:
                data["location_id"] = self.get_location_id(location, db_session)
            sensor = SensorsDB.create(db_session, **data)

            return self.transform_response(sensor)


class Sensor(BaseResource, SensorResourceMixin):
    def get(self, sensor_id, location=None):
        with session_scope(self.config) as db_session:
            sensor = None
            if location:
                query = {"location_id": self.get_location_id(location, db_session), sensors_pk: sensor_id}
                resp = SensorsDB.query(db_session, **query)
                if resp:
                    sensor = resp[0]
            else:
                sensor = SensorsDB.get_by_pkey(db_session, sensor_id)

            if not sensor:
                raise NotFoundError()

            return self.transform_response(sensor)

    @login_required
    def patch(self, sensor_id, location=None):
        with session_scope(self.config) as db_session:
            if location:
                query = {"location_id": self.get_location_id(location, db_session), sensors_pk: sensor_id}
                resp = SensorsDB.query(db_session, **query)
                if resp:
                    sensor = resp[0]
            else:
                sensor = SensorsDB.get_by_pkey(db_session, sensor_id)

            if not sensor:
                raise NotFoundError()

            data = self.get_request_data()
            sensor = SensorsDB.update(db_session, sensor_id, **data)

            return self.transform_response(sensor)

    @login_required
    def delete(self, sensor_id, location=None):
        with session_scope(self.config) as db_session:
            if location:
                query = {"location_id": self.get_location_id(location, db_session), sensors_pk: sensor_id}
                resp = SensorsDB.query(db_session, **query)
                if resp:
                    sensor = resp[0]
            else:
                sensor = SensorsDB.get_by_pkey(db_session, sensor_id)

            if not sensor:
                raise NotFoundError()

            SensorsDB.delete(db_session, sensor_id)

            return True


class SensorData(BaseResource, SensorResourceMixin):
    def get(self, sensor_id, data_type, location=None):
        with session_scope(self.config) as db_session:
            sensor = None
            if location:
                query = {"location_id": self.get_location_id(location, db_session), sensors_pk: sensor_id}
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


class SensorTypes(BaseResource, SensorResourceMixin):
    def get(self):
        return [str(t) for t in get_sensor_types()]
