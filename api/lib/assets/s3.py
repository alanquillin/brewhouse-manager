from lib import aws
from lib.assets import AssetManagerBase


class S3AssetManager(AssetManagerBase):
    def __init__(self):
        super().__init__()
        self.bucket = self.config.get("uploads.s3.bucket.name")
        prefix = self.config.get("uploads.s3.bucket.prefix")
        if prefix:
            prefix = f"{prefix}/"
        else:
            prefix = ""
        self.prefix = prefix

    def _get_object_path(self, image_type, filename):
        return f"{self.prefix}{image_type}/{filename}"

    def _get(self, obj):
        return f"https://{self.bucket}.s3.amazonaws.com/{obj}"

    def get(self, image_type, filename):
        return self._get(self._get_object_path(image_type, filename))

    def list(self, image_type):
        urls = []

        s3 = aws.client("s3")

        pull_more = True
        prefix = f"{image_type}/"
        data = {"Bucket": self.bucket, "Prefix": prefix}
        while pull_more:
            resp = s3.list_objects_v2(**data)
            pull_more = resp.get("IsTruncated")
            contents = resp.get("Contents")

            if contents:
                for obj in contents:
                    key = obj.get("Key")
                    if key == prefix:
                        continue
                    url = self._get(key)
                    if url:
                        urls.append(url)
            data["ContinuationToken"] = resp.get("NextContinuationToken")

        return urls

    def save(self, image_type, file):
        old_filename = file.filename
        filename = self.generate_random_filename(old_filename)
        obj = self._get_object_path(image_type, filename)

        s3 = aws.client("s3")
        # extra_args = {'ACL': 'public-read'}
        extra_args = {}

        # Handle both werkzeug FileStorage (Flask) and FastAPI UploadFile
        if hasattr(file, "file"):
            # FastAPI UploadFile - use the .file attribute
            file_obj = file.file
        else:
            # Flask werkzeug FileStorage - use directly
            file_obj = file

        s3.upload_fileobj(file_obj, self.bucket, obj, ExtraArgs=extra_args)

        return old_filename, filename, self._get(obj)
