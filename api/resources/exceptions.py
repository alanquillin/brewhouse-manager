class UserMessageError(Exception):
    def __init__(self, response_code, user_msg=None, server_msg=None):
        self.user_msg = user_msg or ""
        self.server_msg = server_msg or self.user_msg
        self.response_code = response_code
        super().__init__()


class ClientError(UserMessageError):
    def __init__(self, response_code=400, user_msg=None, **kwargs):
        if not user_msg:
            user_msg = "Invalid request"
        super().__init__(response_code, user_msg=user_msg, **kwargs)


class ServerError(UserMessageError):
    def __init__(self, response_code=500, user_msg=None, server_msg=None):
        user_msg = f"An error occurred while processing the request{f': {user_msg}' if user_msg else ''}"
        server_msg = f"Server-side error while processing request: {server_msg or user_msg}"
        super().__init__(response_code, user_msg=user_msg, server_msg=server_msg)


class NotFoundError(UserMessageError):
    def __init__(self, user_msg=None, **kwargs):
        if not user_msg:
            user_msg = "Requested resource not found"
        super().__init__(404, user_msg=user_msg, **kwargs)


class NotAuthorizedError(ClientError):
    def __init__(self, user_msg=None, **kwargs):
        if not user_msg:
            user_msg = "You are not authorized.  Please login first."
        super().__init__(response_code=401, user_msg=user_msg, **kwargs)

class ForbiddenError(ClientError):
    def __init__(self, user_msg=None, **kwargs):
        if not user_msg:
            user_msg = "You are not authorized to access the requested resource."
        super().__init__(response_code=403, user_msg=user_msg, **kwargs)

class NotAllowedError(ClientError):
    def __init__(self, user_msg=None, **kwargs):
        if not user_msg:
            user_msg = "You are not authorized to perform the specified action"
        super().__init__(response_code=405, user_msg=user_msg, **kwargs)


class InvalidEnum(ValueError):
    pass


class InvalidTapType(InvalidEnum):
    def __init__(self, tap_type, message=None):
        if not message:
            message = f"{tap_type} is an invalid tap type"
        super().__init__(message)
        self.tap_type = tap_type


class InvalidSensorType(InvalidEnum):
    def __init__(self, sensor_type, message=None):
        if not message:
            message = f"{sensor_type} is an invalid sensor type"
        super().__init__(message)
        self.sensor_type = sensor_type

class InvalidExternalBrewingTool(InvalidEnum):
    def __init__(self, tool, message=None):
        if not message:
            message = f"{tool} is an invalid external brewing tool"
        super().__init__(message)
        self.tool = tool