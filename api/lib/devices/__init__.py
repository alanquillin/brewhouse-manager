from lib import logging
from lib.devices import particle

LOG = logging.getLogger(__name__)

device_data_functions = {
    "particle": {
        "_default_": {
            "get_details": particle.get_details,
            "get_description": particle.get_description,
            "supports_status_check": particle.supports_status_check,
            "online": particle.online,
        }
    }
}

device_action_functions = {
    "particle": {
        "_default_": {
            "ping": particle.ping,
            "set_program": particle.set_program,
            "set_target_temp": particle.set_target_temp,
            "refresh_config": particle.refresh_config,
        }
    }
}


def _execute(func_name, func_set, device, *args, **kwargs):
    manufacturer = device.manufacturer.lower()
    model = device.model.lower()

    manufacturer_funcs = func_set.get(manufacturer)
    if not manufacturer_funcs:
        LOG.info("no functions configured for devices with manufacturer: %s", manufacturer)
        return

    model_funcs = manufacturer_funcs.get(model)
    if not model_funcs:
        model_funcs = manufacturer_funcs.get("_default_")

    if not model_funcs:
        LOG.info("no functions configured for %s devices with model: %s", manufacturer, model)
        return

    fn = model_funcs.get(func_name)
    if not fn:
        LOG.info("no %s function configured for %s devices with model: %s", func_name, manufacturer, model)
        return

    return fn(device, *args, **kwargs)


def run(device, func_name, *args, **kwargs):
    return _execute(func_name, device_action_functions, device, *args, **kwargs)


def get(device, func_name, *args, **kwargs):
    return _execute(func_name, device_data_functions, device, *args, **kwargs)


def ping(device, *args, **kwargs):
    return run(device, "ping", *args, **kwargs)


def get_details(device, *args, **kwargs):
    return get(device, "get_details", *args, **kwargs)


def get_description(device, *args, **kwargs):
    return get(device, "get_description", *args, **kwargs)


def supports_status_check(device, *args, **kwargs):
    # There is a chance the implementation return None or other falsey values, so explicitely check for True
    return True if get(device, "supports_status_check", *args, **kwargs) == True else False


def set_program(device, program, *args, **kwargs):
    return run(device, "set_program", program, *args, **kwargs)


def set_target_temp(device, program, *args, **kwargs):
    return run(device, "set_target_temp", program, *args, **kwargs)


def refresh_config(device, *args, **kwargs):
    return run(device, "refresh_config", *args, **kwargs)
