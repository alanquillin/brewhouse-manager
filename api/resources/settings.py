from flask_login import login_required

from resources import BaseResource, ResourceMixinBase

class Settings(BaseResource, ResourceMixinBase):
    def get(self):
        data = {
            "googleSSOEnabled": self.config.get("auth.oidc.google.enabled")
        }
        return data