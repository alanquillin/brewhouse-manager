class Error(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class InvalidEnum(ValueError):
    pass


class InvalidParameter(Error):
    def __init__(self, param, allowed_params=None):
        message = f"Parameter {param} is not allowed."
        if allowed_params:
            message = f"Parameter {param} is not allowed.  Accepted parameters include: [{','.join(allowed_params)}]"
        super().__init__(message)
        self.param = param
        self.allowed_params = allowed_params


class RequiredParameterNotFound(Error):
    def __init__(self, param):
        message = f"Required parameter {param} was not provided."
        super().__init__(message)
        self.param = param


class ItemAlreadyExists(Error):
    def __init__(self, message=None):
        if not message:
            message = "An item already exists with the given key"

        super().__init__(message)


class InvalidExternalBrewingTool(Error):
    def __init__(self, name, message=None):
        if not message:
            message = f"Invalid external brewing tool: {name}"

        super().__init__(message)
        self.name = name


class InvalidTapMonitorType(Error):
    def __init__(self, monitor_type, message=None):
        if not message:
            message = f"Invalid tap monitor type: {monitor_type}"

        super().__init__(message)
        self.monitor_type = monitor_type
