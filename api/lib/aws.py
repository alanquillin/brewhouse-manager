import functools
import uuid

import boto3

from lib import logging
from lib.config import Config

CONFIG = Config()

LOG = logging.getLogger(__name__)

VALUE_NOT_SET = "__VALUE_NOT_SET__"

common_allowed_params = ["aws_access_key_id", "aws_secret_access_key", "aws_session_token", "region_name"]
allowed_session_params = ["assume_role_arn", "assume_role_external_id", "profile_name"]
allowed_client_params = ["api_version", "use_ssl", "verify", "endpoint_url", "config"]


def _extract_params(config_keys, allowed_params, kwargs, params=None):
    if not params:
        params = {}

    for _param in allowed_params:
        for _key in config_keys:
            _key = _key.format(_param)
            _val = CONFIG.get(_key) or VALUE_NOT_SET

            if not _val == VALUE_NOT_SET:
                params[_param] = _val
    params.update({key: val for key, val in kwargs.items() if key in allowed_params})

    return params


def get_assume_role_creds(assume_role_arn, assume_role_external_id=None, session_name=None, **kwargs):
    """
    Retrieves the credentials required to assume the give role and returns a dict that can be passed to boto3

    Args:
        assume_role_arn (str): The ARN for the IAM role that is to be assumed
        session_name (str) [optional]: The name for the session
        **kwargs: All other parameters to be used when retrieving the credentials.  *Note: These need to valid
                  parameters for a boto3.session.Session, as they will be passed directly to boto3.  Invalid parameters
                  will result in an exception

    Returns:
        (dict): The temporary credentials to assume the role.  These can be passed directly to a boto3 session.

    """

    if not session_name:
        session_name = str(uuid.uuid4())

    config_keys = ["aws.{}", "aws.sts.{}"]
    common_params = _extract_params(config_keys, common_allowed_params, kwargs)
    session_params = _extract_params(config_keys, ["profile_name"], kwargs, params={**common_params})
    sts_params = _extract_params(config_keys, allowed_client_params, kwargs, params={**common_params})

    session = boto3.session.Session(**session_params)
    sts_client = session.client("sts", **sts_params)

    assume_role_params = {"RoleArn": assume_role_arn, "RoleSessionName": session_name}
    if assume_role_external_id:
        assume_role_params["ExternalId"] = assume_role_external_id

    assumed_role = sts_client.assume_role(**assume_role_params)

    credentials = assumed_role["Credentials"]
    return {
        "aws_access_key_id": credentials["AccessKeyId"],
        "aws_secret_access_key": credentials["SecretAccessKey"],
        "aws_session_token": credentials["SessionToken"],
    }


def get_session(assume_role_arn=None, assume_role_external_id=None, session_name=None, **kwargs):
    """
    Creates a new boto3.session.Session

    Args:
        assume_role_arn (str) [optional]: The ARN for an IAM role if one is to be assumed
        assume_role_external_id (str) [optional]: The external_id to use when assuming the role.
        session_name (str) [optional]: The name for the session
        **kwargs: Session parameters. *Note: These need to valid parameters for a boto3.session.Session, as they will
                  be passed directly to boto3.  Invalid parameters will result in an exception

    Returns:
        (boto3.session.Session): The boto3 Session object

    """

    if not session_name:
        session_name = str(uuid.uuid4())

    if assume_role_arn:
        creds = get_assume_role_creds(
            assume_role_arn,
            assume_role_external_id=assume_role_external_id,
            session_name=f"{session_name}-assume",
            **kwargs,
        )
    else:
        creds = kwargs

    return boto3.session.Session(**creds)


def sessionized(func):
    @functools.wraps(func)
    def wrapper(name, session=None, **kwargs):
        """
        Builds the parameters and session (if one is not provided) to create the boto3 Resource and Client APIs.

        The parameters can either be passed in via the method kwargs, or set in the config under the "aws" section.
        If setting the parameters via the config, the keys much match the name of the parameter to set.  Take care when
        setting these in the config as they will be applied globally (unless explicitely overwritten) to all sessions,
        clients and resources created. You can set the config values in 2 ways, in the "aws" section, or the
        "aws.{name}" section.  The values set in the "aws.{name}" section will override values set in the "aws" section.

        Example config:
        {
            "aws": {
                "profile_name": "my-profile",
                "s3": {
                    "profile_name": null,
                    "aws_access_key_id: "abc123",
                    "aws_secret_access_key": "secret-abc123"
                }
            }
        }

        For the above config, all resources or clients (except s3) will use the "my-profile" profile.
        For s3, this removes the profile and instead will use the configured access/secret key pair.

        All parameters passed in via the kwargs will override those set in the config.  To remove a value and set it
        back to the default, explicitely set the value to false.

        Example overriding the above config values:
        s3 = aws.resource("s3", endpoint_url=None, assume_role_arn=None, profile_name="my-profile")

        In the above example, a s3 resource will be created and will use the default endpoint url and no longer
        use an assumed role.  Instead, it will use the "my-profile" profile.

        Args:
            name (str) [optional]: The name of the resource/client
            session (botocore.Session) [optional]: An existing boto3.session.Session object.
            **kwargs: Parameters. *Note: These can be any valid parameters for the boto3.session.Session or the
                      boto3.session.Session.[client,resource] apis.  All invalid parameters will be ignored.

        """

        config_keys = ["aws.{}", "aws.%s.{}" % name]  # pylint: disable=consider-using-f-string
        common_params = _extract_params(config_keys, common_allowed_params, kwargs)

        if not session:
            session_params = _extract_params(config_keys, allowed_session_params, kwargs, params={**common_params})
            session = get_session(**session_params)

        params = _extract_params(config_keys, allowed_client_params, kwargs, params={**common_params})
        return func(name, session=session, **params)

    return wrapper


@sessionized
def resource(resource_name, session=None, **kwargs):
    """
    Wrapper for boto3.resource

    Args:
        resource_name (str) [optional]: The name for the resource type
        **kwargs: Parameters. *Note: These can be any valid parameters for the boto3.session.Session or the
                      boto3.session.Session.[client,resource] apis.  All invalid parameters will be ignored.

    Returns:
        (boto3.resource): The boto3 Resource object

    """

    return session.resource(resource_name, **kwargs)


@sessionized
def client(client_name, session=None, **kwargs):
    """
    Wrapper for boto3.client

    Args:
        resource_name (str) [optional]: The name for the client type
        **kwargs: Parameters. *Note: These can be any valid parameters for the boto3.session.Session or the
                      boto3.session.Session.[client,resource] apis.  All invalid parameters will be ignored.

    Returns:
        (boto3.resource): The boto3 Client object

    """

    return session.client(client_name, **kwargs)
