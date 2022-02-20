import json
import logging
import os

from lib import Error, ThreadSafeSingleton
from lib.util import flatten_dict


class RequiredConfigKeyNotFound(Error):
    def __init__(self, key, message=None):
        if not message:
            message = f"Config key '{key}' is required but not provided"
        super().__init__(message)
        self.key = key


class RequiredConfigKeysNotFound(Error):
    def __init__(self, keys, message=None):
        if not message:
            message = f"The following config keys are required but not provided: {keys}"
        super().__init__(message)
        self.missing_keys = keys


def value_converter(func):
    def wrapper(val, *args):
        if val is None:
            return val

        return func(val, *args)

    return wrapper


@value_converter
def to_int(val, *_):
    if isinstance(val, int):
        return val

    return int(val)


@value_converter
def to_bool(val, *_):
    if isinstance(val, bool):
        return val

    return val.lower() == "true"


@value_converter
def to_list(val, *args):
    if isinstance(val, str):
        sep = ","
        if args:
            sep = args[0]
        return val.split(sep)

    return list(val)


@value_converter
def to_dict(val, *args):
    if isinstance(val, str):
        data = {}
        sep = ","
        if args:
            sep = args[0]
        for item in val.trim().split(sep):
            sep2 = "="
            if args and len(args) > 1:
                sep2 = args[1]
            parts = item.trim().split(sep2)
            data[parts[0].trim()] = parts[1].trim()
        return data

    return dict(val)


class Config(metaclass=ThreadSafeSingleton):
    defaults = {
        "db": {"username": "brew_user", "host": "localhost", "port": 5432, "name": "brewhouse"},
        "log_level": "",
    }

    default_schema = {"db.port": "int", "logging.levels": "dict"}

    key_aliases = {"APP_ID": ["brewhouse-manager"]}
    type_conversions = {"int": to_int, "bool": to_bool, "list": to_list, "dict": to_dict}

    def __init__(self, **kwargs):
        self.logger = logging.getLogger("config")

        self.setup(**kwargs)

    def _flatten_config_data(self, data):
        return flatten_dict(
            data,
            self.env_prefix,
            key_converter=lambda k: k.replace(".", "_").upper(),
            skip_key_check=lambda k: self.gen_key(k) in self.conversion_schema,
        )

    def _load_conf(self, data):
        if not data:
            return

        schema = data.pop("__conversion_schema", {})
        if schema:
            self.conversion_schema.update(self._process_conversion_schema(schema))

        self.data_flat.update(self._flatten_config_data(data))

    def _load_config_file(self, config_file, base_dir):
        path = os.path.normpath(os.path.join(base_dir, config_file))
        self.logger.debug("Loading config file: %s", path)
        with open(path, "r") as config:
            self._load_conf(json.loads(config.read()))

    def _verify_required_keys(self, required_keys):
        if not required_keys:
            return

        missing_keys = []
        for key in required_keys:
            _key = self.gen_key(key)
            if not _key in self.data_flat and _key not in os.environ and _key not in self.explicit_configs:
                missing_keys.append(key)

        if missing_keys:
            raise RequiredConfigKeysNotFound(missing_keys)

    def _process_conversion_schema(self, schema):
        if not schema:
            return {}

        return {self.gen_key(k): v for k, v in schema.items()}

    def gen_key(self, key):
        return f"{self.key_prefix}{key}".replace(".", "_").replace("-", "_").upper()

    def setup(  # pylint: disable=too-many-arguments
        self,
        env_prefix="",
        config_files=None,
        base_dir=None,
        required_keys=None,
        config_overrides=None,
        conversion_schema=None,
        explicit_configs=None,
    ):
        if not config_files:
            config_files = []

        if not conversion_schema:
            conversion_schema = {}

        if not explicit_configs:
            explicit_configs = {}

        key_prefix = ""
        if env_prefix:
            key_prefix = f"{env_prefix}_"

        self.env_prefix = env_prefix
        self.key_prefix = key_prefix
        self.conversion_schema = self._process_conversion_schema(self.default_schema)
        self.conversion_schema.update(self._process_conversion_schema(conversion_schema))
        self.explicit_configs = self._flatten_config_data(explicit_configs)

        self.data_flat = {}
        self._load_conf(self.defaults)
        self._load_conf(config_overrides)

        config_path = os.environ.get(self.gen_key("CONFIG_PATH"))
        if config_path:
            config_files.append(config_path)

        base_dir = os.environ.get(self.gen_key("CONFIG_BASE_DIR"), os.path.dirname(os.path.abspath(__file__)) if not base_dir else base_dir)
        self.set("CONFIG_BASE_DIR", base_dir)

        for config_file in config_files:
            self._load_config_file(config_file, base_dir)

        self._verify_required_keys(required_keys)

    def get(self, key, default=None, required=False):
        keys = [key] + self.key_aliases.get(key.upper(), [])

        for k in keys:
            _key = self.gen_key(k)
            result = self.explicit_configs.get(_key, os.environ.get(_key, self.data_flat.get(_key)))
            if result:
                break
        if result is None:
            result = default

        if required and result is None:
            raise RequiredConfigKeyNotFound(key)

        conversion_scheme = self.conversion_schema.get(_key)

        if conversion_scheme:
            parts = conversion_scheme.split("|")
            conversion_type = parts[0]
            conversion_args = () if len(parts) == 1 else tuple(parts[1:])
            converter = self.type_conversions.get(conversion_type)

            if not converter:
                self.logger.warning("No value converter for type: %s", conversion_type)
            else:
                return converter(result, *conversion_args)

        if not result:
            children = {k: v for k, v in self.data_flat.items() if k.startswith(f"{_key}_")}
            if children:
                self.logger.debug(
                    ("No value found for key '%s', but child values were found.  " "Assuming the caller wanted a dict, so returning a ConfigHelper"),
                    key,
                )
                return self.get_helper(key)

        return result

    def assert_keys_exist(self, expected_keys):
        self._verify_required_keys(expected_keys)

    def set(self, key, value):
        self.data_flat[self.gen_key(key)] = value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def get_helper(self, prefix):
        return ConfigHelper(prefix, self)

    def __str__(self):
        return json.dumps(self.data_flat, indent=2)


class ConfigHelper:
    def __init__(self, prefix, config):
        self.prefix = prefix
        self.config = config

    def _get_key(self, key):
        if not self.prefix:
            return key

        return f"{self.prefix}.{key}"

    def set(self, key, value):
        self.config.set(self._get_key(key), value)

    def get(self, key, default=None, required=False):
        return self.config.get(self._get_key(key), default=default, required=required)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def __str__(self):
        data = {k: v for k, v in self.config.data_flat.items() if k.startswith(f"{self.config.gen_key(self.prefix)}_")}

        return json.dumps(data, indent=2)
