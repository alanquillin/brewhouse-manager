import os

from lib.assets import AssetManagerBase


class FileAssetManager(AssetManagerBase):
    def __init__(self):
        super().__init__()
        self.assets_base_dir = self.config.get("uploads.base_dir")

    def get_parent_dir(self, image_type):
        return os.path.join(self.assets_base_dir, "img", image_type)

    def get(self, image_type, filename):
        return f"/assets/uploads/img/{image_type}/{filename}"

    def list(self, image_type):
        parent_path = self.get_parent_dir(image_type)
        all_files = [f for f in os.listdir(parent_path) if os.path.isfile(os.path.join(parent_path, f))]
        return [self.get(image_type, f) for f in all_files if not f.startswith(".")]

    def save(self, image_type, file):
        old_filename = file.filename
        filename = self.generate_random_filename(old_filename)

        parent_dir = self.get_parent_dir(image_type)
        if not os.path.exists(parent_dir):
            self.logger.debug("Image director `%s` does not exist.  Creating...", parent_dir)
            os.makedirs(parent_dir)
            self.logger.debug("Successfully created dir '%s'!", parent_dir)

        path = os.path.join(parent_dir, filename)

        # Handle both werkzeug FileStorage (Flask) and FastAPI UploadFile
        if hasattr(file, "save"):
            # Flask werkzeug FileStorage
            file.save(path)
        else:
            # FastAPI UploadFile - write contents to disk
            with open(path, "wb") as f:
                contents = file.file.read()
                f.write(contents)
            # Reset file pointer for potential reuse
            file.file.seek(0)

        return old_filename, filename, self.get(image_type, filename)
