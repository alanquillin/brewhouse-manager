from lib.exceptions import Error


class TapMonitorDependencyError(Error):
    def __init__(self, monitor_type, message=None):
        self.monitor_type = monitor_type
        if not message:
            message = f"Unknown error for {monitor_type} when calling dependent service"
        super().__init__(message)
