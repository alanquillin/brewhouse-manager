from flask_login import login_required

from lib import external_brew_tools
from resources import BaseResource, ResourceMixinBase


class ExternalBrewToolTypes(BaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        return [t for t in external_brew_tools.get_types()]


class ExternalBrewTool(BaseResource, ResourceMixinBase):
    @login_required
    def get(self, tool_name):
        tool = external_brew_tools.get_tool(tool_name)
        return tool._say_hello()


class SearchExternalBrewTool(BaseResource, ResourceMixinBase):
    @login_required
    def get(self, tool_name):
        tool = external_brew_tools.get_tool(tool_name)
        return [self.transform_response(b) for b in tool.list()]
