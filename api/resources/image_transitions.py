from flask_login import login_required

from db import session_scope
from db.sensors import _PKEY as sensors_pk
from db.image_transitions import ImageTransitions as ImageTransitionsDB
from resources import BaseResource, NotFoundError


class ImageTransition(BaseResource):
    @login_required
    def delete(self, image_transition_id, location=None):
        with session_scope(self.config) as db_session:
            sensor = ImageTransitionsDB.get_by_pkey(db_session, image_transition_id)

            if not sensor:
                raise NotFoundError()

            ImageTransitionsDB.delete(db_session, image_transition_id)

            return True
