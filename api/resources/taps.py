from resources import BaseResource, ResourceMixinBase, NotFoundError
from db import session_scope
from db.locations import Locations as LocationsDB
from db.taps import Taps as TapsDB, _PKEY as taps_pk

class Taps(BaseResource, ResourceMixinBase):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            if location:
                location_id = self.get_location_id(location, db_session)
                taps = TapsDB.get_by_location(db_session, location_id)
            else:
                taps = TapsDB.query(db_session)
            return [self.transform_response(t.to_dict()) for t in taps]


class Tap(BaseResource, ResourceMixinBase):
    def get(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            tap = None
            if location:
                query = {
                    "location_id": self.get_location_id(location, db_session),
                    taps_pk: tap_id
                }
                res = TapsDB.query(db_session, **query)
                if res:
                    tap = res[0]
            else:    
                tap = TapsDB.get_by_pkey(db_session, tap_id)
            
            if not tap:
                raise NotFoundError()
                
            return self.transform_response(tap.to_dict())