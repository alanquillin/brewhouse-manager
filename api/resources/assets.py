import os
from uuid import uuid4

from flask import redirect, request
from flask_login import (
    login_required
)
from werkzeug.utils import secure_filename

from resources import BaseResource, ResourceMixinBase, ClientError, ClientError
from db import session_scope

class UploadImage(BaseResource, ResourceMixinBase):
    def __init__(self):
        super().__init__()
        self.assets_base_dir = self.config.get("uploads.base_dir")
        self.allowed_image_extensions = self.config.get("uploads.images.allowed_file_extensions")
    
    @staticmethod
    def get_file_extension(filename):
        return filename.rsplit('.', 1)[1].lower()
    
    def is_file_allowed(self, filename):
        return '.' in filename and self.get_file_extension(filename) in [e.replace(".", "") for e in self.allowed_image_extensions]
    
    @login_required
    def post(self, image_type):
        if image_type not in ["beer", "user"]:
            raise ClientError(user_msg=f"Invalid image type '{image_type}'.  Must be either 'beer' or 'user'")

        if 'file' not in request.files:
            raise ClientError(user_msg="File part missing in request.")

        file = request.files['file']
        
        if not file or file.filename == '':
            raise ClientError(user_msg="File is missing in the request.")
        
        if not self.is_file_allowed(file.filename):
            raise ClientError(user_msg=f"Invalid file type.  Must be one of: {', '.join(self.allowed_image_extensions)}")

        old_filename = file.filename
        new_filename = f"{str(uuid4())}.{self.get_file_extension(old_filename)}"
        filename = secure_filename(new_filename)
        
        parent_dir = os.path.join(self.assets_base_dir, "img", image_type)
        if not os.path.exists(parent_dir):
            self.logger.debug("Image director `%s` does not exist.  Creating...", parent_dir)
            os.makedirs(parent_dir)
            self.logger.debug("Successfully created dir '%s'!", parent_dir)
        
        self.logger.info("Saving uploaded file '%s' as '%s'", old_filename, filename)
        path = os.path.join(parent_dir, filename)
        file.save(path)
        self.logger.debug("Successfully saved file '%s'", path)
        
        return {"sourceFilename": old_filename, "destinationFilename": filename}
