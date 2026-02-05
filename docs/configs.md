# Configuration

## Setting configuration options

There are 2 ways to set configuration options:

1. Environment variables
2. Optional configuration file (json)

Configuration options are defined in this doc with a `.` separating sections with the last part being the key.
These sections are then defined in the configuration file hierarchy.  So for example: `app.group1.my_setting` would be
defined in the config file as:


```json
{
    "app": {
        "group1": {
            "my_setting": "value"
        }
    }
}
```

To use a configuration file, the file needs to be mounted into the container in the `/brewhouse-manager/config` directory.
The `CONFIG_PATH` environment variable then needs to be set to the name of the config file.  If you mounted the file into a
subdirectory of the containers `/brewhouse-manager/config` directory, then the `CONFIG_PATH` variable should also
contain the relative path.  Example:  If you mount a file called `config.json` into the container at
`/brewhouse-manager/config/custom/mine/config.json`, then you would set the environment variable to
`CONFIG_PATH=custom/mine/config.json`

### Environment Variables

To set the configuration value using an environment variable, you just replace the `.`s with `_`s and capitalize it.  The example above
would be:

```shell
APP_GROUP1_MY_SETTING=value
```

## Configuration value precedence

If a configuration value is set in multiple places, the order of precedence is:
__enviornment variable__ -> __optional configuration file__ -> __default configuration file__

## Configuration Options

### General application settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `app.secret_key` | `string` | N | | A unique string used for signing the session cookies.  This is optional, and if not provided, one will be randomly generated when the server starts |
| `api.port` | `integer` | N | `5000` | The port number for the web server |
| `logging.level` | `string` | N | `INFO` | The logging level to set.  Valid values are: `[DEBUG, INFO, WARNING, ERROR]` |
| `logging.levels.[package name]` | `string` | N | | The log level to set for a specific python dependency/package.  Ex: `urllib3` |

### Authentication settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `auth.initial_user.email` | `string` | N | `default_admin@acme.fake` | The email address for the initial user created.  This user is only created the first time the application boots up and there are no other users in the database. |
| `auth.initial_user.first_name` | `string` | N | `INITIAL` | THe first name of the initial user |
| `auth.initial_user.last_name` | `string` | N | `ADMIN` | The last name of the initial user |
| `auth.initial_user.password` | `string` | N | `initial_password` | The password to be set for the initial user.  This is only set of the `auth.initial_user.set_password` is `true` |
| `auth.initial_user.set_password` | `boolean` | N | `true` | Sets the password for the initial user.  If `false`, the Google OpenID Connect provider provider needs to be enabled |
| `auth.oidc.google.client_id` | `string` | N | | The client id used for the Google OpenID Connect provider |
| `auth.oidc.google.client_secret` | `string` | N | | The client secret used for the Google OpenID Connect provider |
| `auth.oidc.google.discovery_url` | `string` | N | `https://accounts.google.com/.well-known/openid-configuration` | The discovery URL used for the Google OpenID Connect provider |
| `auth.oidc.google.enabled` | `boolean` | N | `false` | Enables the ability to login using Google OpenID Connect provider |

### Database settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `db.username` | `string` | Y | `brew_user` | The username for connecting to the backend PostgreSQL database |
| `db.password` | `string` | Y | | The password for connecting to the backend PostgreSQL database |
| `db.host` | `string` | Y | `localhost` | The hostname for connecting to the backend PostgreSQL database |
| `db.port` | `integer` | Y | `5432` | The port for connecting to the backend PostgreSQL database |
| `db.name` | `string` | Y | `brewhouse` | The name of the backend PostgreSQL database |

### Integrations

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `external_brew_tools.brewfather.enabled` | `boolean` | N | `false` | Enables the integration with [brefather](https://brewfather.app) |
| `external_brew_tools.brewfather.username` | `string` | N |  | The brewfather API username (required if `external_brew_tools.brewfather.enabled` is `true`) |
| `external_brew_tools.brewfather.api_key` | `string` | N |  | The brewfather API key (required if `external_brew_tools.brewfather.enabled` is `true`) |

### Sensor Settings

#### Plaato Keg (Native Integration)

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `sensors.plaato_keg.enabled` | `boolean` | N | `false` | Enables native Plaato Keg integration. When enabled, starts a TCP server that Plaato Keg devices can connect to directly. |
| `sensors.plaato_keg.host` | `string` | N | `localhost` | The hostname/IP address for the TCP server to bind to. Use `0.0.0.0` to accept connections from external devices on your network. |
| `sensors.plaato_keg.port` | `integer` | N | `5001` | The TCP port for the server to listen on. Plaato Keg devices must be configured to connect to this port. |

**Example Configuration:**

Using environment variables:
```bash
SENSORS_PLAATO_KEG_ENABLED=true
SENSORS_PLAATO_KEG_HOST=0.0.0.0
SENSORS_PLAATO_KEG_PORT=5001
```

Using config file (config.json):
```json
{
  "sensors": {
    "plaato_keg": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 5001
    }
  }
}
```

**Device Setup:**
1. Enable the integration using the configuration above
2. Navigate to `/manage/plaato_kegs` in the web UI (admin access required)
3. Click "Setup New Device" and follow the instructions to:
   - Reset your Plaato Keg device
   - Configure device WiFi settings
   - Set the device to connect to your Brewhouse Manager server at the configured host:port
   - Register the device in the system

Once configured, devices will automatically connect and begin streaming sensor data.