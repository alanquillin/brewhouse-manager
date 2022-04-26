from flask_login import login_required

from resources import ResourceMixinBase, UIBaseResource

class RestrictedGenericPageHandler(UIBaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return self.serve_app()

class GenericPageHandler(UIBaseResource, ResourceMixinBase):
    def get(self):
        return self.serve_app()