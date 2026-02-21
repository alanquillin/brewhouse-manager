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
| `app.secret_key` | `string` | N | _auto-generated_ | A unique string used for signing the session cookies.  This is optional, and if not provided, one will be randomly generated when the server starts |
| `app_id` | `string` | N | `brewhouse-manager` | The application identifier |
| `api.host` | `string` | N | `localhost` | The hostname/IP address for the web server to bind to |
| `api.port` | `integer` | N | `5000` | The port number for the web server |
| `api.schema` | `string` | N | `http` | The URL schema to use (http or https) |
| `api.cookies.secure` | `boolean` | N | `true` | Whether to set the Secure flag on session cookies (requires HTTPS) |
| `api.cookies.http_only` | `boolean` | N | `true` | Whether to set the HttpOnly flag on session cookies (prevents JavaScript access) |
| `api.cookies.samesite` | `string` | N | `lax` | SameSite cookie attribute. Valid values: `strict`, `lax`, `none` |
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

### Dashboard settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `dashboard.refresh_sec` | `integer` | N | `15` | The refresh interval in seconds for the dashboard display |

### Beverages settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `beverages.default_type` | `string` | N | `cold-brew` | The default beverage type for new beverages |
| `beverages.supported_types` | `list` | N | `["cold-brew", "soda", "kombucha"]` | List of supported beverage types |

### Taps settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `taps.refresh.base_sec` | `integer` | N | `300` | Base refresh interval in seconds for tap status updates |
| `taps.refresh.variable` | `integer` | N | `150` | Variable refresh interval in seconds added to the base for randomization |

### Integrations

#### Brewfather

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `external_brew_tools.brewfather.enabled` | `boolean` | N | `false` | Enables the integration with [brewfather](https://brewfather.app) |
| `external_brew_tools.brewfather.username` | `string` | N |  | The brewfather API username (required if `external_brew_tools.brewfather.enabled` is `true`) |
| `external_brew_tools.brewfather.api_key` | `string` | N |  | The brewfather API key (required if `external_brew_tools.brewfather.enabled` is `true`) |
| `external_brew_tools.brewfather.completed_statuses` | `list` | N | `["Completed", "Archived", "Conditioning"]` | List of batch statuses considered as completed |
| `external_brew_tools.brewfather.refresh_buffer_sec.soft` | `integer` | N | `1200` | Soft refresh buffer in seconds (20 minutes) |
| `external_brew_tools.brewfather.refresh_buffer_sec.hard` | `integer` | N | `120` | Hard refresh buffer in seconds (2 minutes) |

### Upload/Asset Management

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `uploads.storage_type` | `string` | N | `local_fs` | Storage backend for uploaded files. Valid values: `local_fs`, `s3` |
| `uploads.base_dir` | `string` | N | `/brewhouse-manager/api/static/assets/uploads` | Base directory for local file storage (only used when `storage_type` is `local_fs`) |
| `uploads.images.allowed_file_extensions` | `list` | N | `["jpg","jpeg","png","gif","svg"]` | List of allowed file extensions for image uploads |
| `uploads.s3.bucket.name` | `string` | N | | S3 bucket name (required when `storage_type` is `s3`) |
| `uploads.s3.bucket.prefix` | `string` | N | | Optional prefix/folder path within the S3 bucket |

### AWS Configuration

When using S3 for asset storage, you can configure AWS credentials and settings. These settings follow standard boto3 configuration patterns.

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `aws.profile_name` | `string` | N | | AWS profile name to use from ~/.aws/credentials |
| `aws.aws_access_key_id` | `string` | N | | AWS access key ID |
| `aws.aws_secret_access_key` | `string` | N | | AWS secret access key |
| `aws.aws_session_token` | `string` | N | | AWS session token (for temporary credentials) |
| `aws.region_name` | `string` | N | | AWS region name |
| `aws.s3.[param]` | various | N | | S3-specific overrides (can override any of the above for S3 operations) |

**Note:** AWS credentials can also be provided via standard AWS environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc.) or IAM roles when running in AWS.

### Tap Monitor Settings

#### General Tap Monitor Settings

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `tap_monitors.preferred_vol_unit` | `string` | N | `gal` | Preferred volume unit for tap monitor data. Valid values: `gal`, `l` |

#### Plaato Keg (Native Integration)

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `tap_monitors.plaato_keg.enabled` | `boolean` | N | `false` | Enables native Plaato Keg integration. When enabled, starts a TCP server that Plaato Keg devices can connect to directly. |
| `tap_monitors.plaato_keg.host` | `string` | N | `localhost` | The hostname/IP address for the TCP server to bind to. Use `0.0.0.0` to accept connections from external devices on your network. |
| `tap_monitors.plaato_keg.port` | `integer` | N | `5001` | The TCP port for the server to listen on. Plaato Keg devices must be configured to connect to this port. |

**Example Configuration:**

Using environment variables:
```bash
TAP_MONITORS_PLAATO_KEG_ENABLED=true
TAP_MONITORS_PLAATO_KEG_HOST=0.0.0.0
TAP_MONITORS_PLAATO_KEG_PORT=5001
```

Using config file (config.json):
```json
{
  "tap_monitors": {
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

#### Open Plaato Keg

Integration with the [open-plaato-keg](https://github.com/sklopivo/open-plaato-keg) service for legacy Plaato Keg support.

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `tap_monitors.open_plaato_keg.enabled` | `boolean` | N | `false` | Enables integration with open-plaato-keg service. Requires open-plaato-keg version 0.0.11+ to be running separately. |
| `tap_monitors.open_plaato_keg.insecure` | `boolean` | N | `false` | Disable SSL certificate verification when connecting to open-plaato-keg service |

#### Plaato Blynk

Legacy Plaato tap monitor integration via Blynk protocol (for older Plaato Airlock devices).

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `tap_monitors.plaato_blynk.enabled` | `boolean` | N | `false` | Enables Plaato Blynk tap monitor integration |

#### Kegtron Pro

Integration with [Kegtron Pro](https://kegtron.com/pro/) keg monitoring devices.

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `tap_monitors.kegtron.pro.enabled` | `boolean` | N | `false` | Enables Kegtron Pro tap monitor integration |

#### Keg Volume Monitors

Integration with [DIY Keg Volume Monitors](https://github.com/alanquillin/keg-volume-monitors).

| key  | type | required | default | description |
| ---- | ---- | -------- | ------- | ----------- |
| `tap_monitors.keg_volume_monitors.enabled` | `boolean` | N | `false` | Enables DIY Keg Volume Monitor integration (must be enabled for weight or flow tap monitors) |
| `tap_monitors.keg_volume_monitors.weight.enabled` | `boolean` | N | `false` | Enables weight-based keg monitoring (requires `tap_monitors.keg_volume_monitors.enabled` to be `true`) |
| `tap_monitors.keg_volume_monitors.flow.enabled` | `boolean` | N | `false` | Enables flow-based keg monitoring (requires `tap_monitors.keg_volume_monitors.enabled` to be `true`) |