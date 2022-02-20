from flask import request
from flask_login import login_required

from db import session_scope
from db.beers import _PKEY as beers_pk
from db.beers import Beers as BeersDB
from db.locations import Locations as LocationsDB
from lib.external_brew_tools import get_tool as get_external_brewing_tool
from resources import ResourceMixinBase, UIBaseResource


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


class ManagemantUsers(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()


class Home(UIBaseResource, ResourceMixinBase):
    def get(self):
        return self.serve_app()


class LocationView(UIBaseResource, ResourceMixinBase):
    def get(self, **_):
        return self.serve_app()


class Login(UIBaseResource, ResourceMixinBase):
    def get(self):
        return self.serve_app()
