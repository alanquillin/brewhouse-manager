from lib.exceptions import Error


class SensorDependencyError(Error):
    def __init__(self, sensor_type, message=None):
        self.sensor_type = sensor_type
        if not message:
            message = f"Unknown error for {sensor_type} when calling dependent service"
        super().__init__(message)
