from flask import request
from flask_login import login_required

from resources import UIBaseResource, ResourceMixinBase
from db import session_scope
from db.locations import Locations as LocationsDB
from db.beers import Beers as BeersDB, _PKEY as beers_pk
from lib.external_brew_tools import get_tool as get_external_brewing_tool


class ManagemantDashboard(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()

class Profile(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()

class ManagemantLocations(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()

class ManagemantTaps(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()

class ManagemantBeers(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()

class ManagemantSensors(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()