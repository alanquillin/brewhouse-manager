from lib.config import Config
from lib import logging

TOOLS = {}

class ExternalBrewToolBase():
    def __init__(self) -> None:
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

def _init_tools():
    global TOOLS
    if not TOOLS:
        from lib.external_brew_tools.brewfather import Brewfather
        
        TOOLS = {
            "brewfather": Brewfather()
        }

def get_types():
    return TOOLS.keys()

def get_tool(_type):
    return TOOLS.get(_type)

_init_tools()