from flask_login import login_required

from resources import BaseResource, ResourceMixinBase


class Settings(BaseResource, ResourceMixinBase):
    def get(self):
        data = {
            "googleSSOEnabled": self.config.get("auth.oidc.google.enabled"),
            "taps": {"refresh": {"baseSec": self.config.get("taps.refresh.base_sec"), "variable": self.config.get("taps.refresh.variable")}},
            "beverages": {"defaultType": self.config.get("beverages.default_type"), "supportedTypes": self.config.get("beverages.supported_types")},
            "dashboard": {"refreshSec": self.config.get("dashboard.refresh_sec")},
        }
        return data
