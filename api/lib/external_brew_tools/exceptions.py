from lib.exceptions import Error

class ResourceNotFoundError(Error):
    resource_id = None

    def __init__(self, resource_id, message=None):
        self.resource_id = resource_id

        if not message:
            message = f"Resource with id '{resource_id}' could not be found"

        super().__init__(message)