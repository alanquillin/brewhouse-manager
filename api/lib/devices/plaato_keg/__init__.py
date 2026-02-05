from lib import ThreadSafeSingleton
from lib.devices.plaato_keg.connection_handler import ConnectionHandler
from lib.devices.plaato_keg.command_writer import CommandWriter


class PlaatoServiceHandler(metaclass=ThreadSafeSingleton):
    def __init__(self):
        self.connection_handler = ConnectionHandler()
        self.command_writer = CommandWriter(self.connection_handler)


service_handler = PlaatoServiceHandler()