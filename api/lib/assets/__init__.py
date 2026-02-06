from uuid import uuid4

from werkzeug.utils import secure_filename

from lib import logging
from lib.config import Config


class AssetManagerBase:
    def __init__(self) -> None:
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def get_file_extension(filename):
        return filename.rsplit(".", 1)[1].lower()

    @staticmethod
    def generate_random_filename(filename):
        new_filename = f"{str(uuid4())}.{AssetManagerBase.get_file_extension(filename)}"

        return secure_filename(new_filename)
