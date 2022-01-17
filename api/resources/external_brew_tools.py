#from flask_connect import login_required

from resources import BaseResource, ResourceMixinBase
from db import session_scope
from lib import external_brew_tools

class ExternalBrewToolTypes(BaseResource, ResourceMixinBase):
    def get(self):
        return [t for t in external_brew_tools.get_types()]


class ExternalBrewTool(BaseResource, ResourceMixinBase):
    def get(self, tool_name):
        tool = external_brew_tools.get_tool(tool_name)
        return tool._say_hello()

class SearchExternalBrewTool(BaseResource, ResourceMixinBase):
    def get(self, tool_name):
        tool = external_brew_tools.get_tool(tool_name)
        return [self.transform_response(b) for b in tool.list()]
