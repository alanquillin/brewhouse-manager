from flask import request
from flask_login import login_required

from lib.assets.files import FileAssetManager
from lib.assets.s3 import S3AssetManager
from resources import BaseResource, ClientError, ResourceMixinBase

allowed_image_types = ["beer", "user", "beverage"]


class UploadImage(BaseResource, ResourceMixinBase):
    def __init__(self):
        super().__init__()
        
        self.storage_type = self.config.get("uploads.storage_type")
        if self.storage_type.lower() == "s3":
            self.manager = S3AssetManager()
        else:
            self.manager = FileAssetManager()
        
        self.allowed_image_extensions = self.config.get("uploads.images.allowed_file_extensions")

    def is_file_allowed(self, filename):
        return "." in filename and self.manager.get_file_extension(filename) in [e.replace(".", "") for e in self.allowed_image_extensions]

    @login_required
    def get(self, image_type):
        if image_type not in allowed_image_types:
            raise ClientError(user_msg=f"Invalid image type '{image_type}'.  Must be either 'beer', 'beverage' or 'user'")

        return self.manager.list(image_type)

    @login_required
    def post(self, image_type):
        if image_type not in allowed_image_types:
            raise ClientError(user_msg=f"Invalid image type '{image_type}'.  Must be either 'beer', 'beverage' or 'user'")

        if "file" not in request.files:
            raise ClientError(user_msg="File part missing in request.")

        file = request.files["file"]

        if not file or file.filename == "":
            raise ClientError(user_msg="File is missing in the request.")

        if not self.is_file_allowed(file.filename):
            raise ClientError(user_msg=f"Invalid file type.  Must be one of: {', '.join(self.allowed_image_extensions)}")

        self.logger.info("Saving uploaded file '%s'", file.filename)
        of,df,dp = self.manager.save(image_type, file)
        self.logger.debug("Successfully saved file '%s' as '%s'", of, df)

        return {"sourceFilename": of, "destinationPath": dp}
