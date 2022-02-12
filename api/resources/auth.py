from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import redirect, request
from flask_login import (
    login_required,
    login_user,
    logout_user,
    UserMixin
)
import json
from oauthlib.oauth2 import WebApplicationClient
import requests

from resources import BaseResource, ResourceMixinBase, ClientError, NotAuthorizedError, ClientError, ForbiddenError, UIBaseResource
from db import session_scope
from db.users import Users as UsersDB

class AuthUser(UserMixin):
    def __init__(self, id_, first_name, last_name, email, profile_pic, google_oidc_id):
        super().__init__()

        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.profile_pic = profile_pic
        self.google_oidc_id = google_oidc_id

    @staticmethod
    def from_user(user):
        if not user:
            return None
            
        return AuthUser(
            user.id,
            user.first_name,
            user.last_name,
            user.email,
            user.profile_pic,
            user.google_oidc_id
        )

class GoogleResourceMixin(ResourceMixinBase):
    def __init__(self):
        super().__init__()
        self.client_id = self.config.get("auth.oidc.google.client_id")
        self.client_secret = self.config.get("auth.oidc.google.client_secret")
        self.discovery_url = self.config.get("auth.oidc.google.discovery_url")
        
        self.client = WebApplicationClient(self.client_id)

    def get_provider_cfg(self):
        return requests.get(self.discovery_url).json()

class GoogleLogin(BaseResource, GoogleResourceMixin):
    def get(self):
        if not self.config.get("auth.oidc.google.enabled"):
            raise ForbiddenError(user_msg="Google authentication is disabled")

        # Find out what URL to hit for Google login
        google_provider_cfg = self.get_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        request_uri = self.client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        self.logger.debug("redirecting to google SSO: %s", request_uri)
        return redirect(request_uri)

class GoogleCallback(UIBaseResource, GoogleResourceMixin):
    def get(self):
        # Get authorization code Google sent back to you
        code = request.args.get("code")

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = self.get_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = self.client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.client_id, self.client_secret),
        )

        # Parse the tokens!
        self.client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = self.client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        userinfo = userinfo_response.json()
        self.logger.debug("user info: %s", userinfo)
        if userinfo.get("email_verified"):
            unique_id = userinfo.get("sub")
            users_email = userinfo.get("email")
            picture = userinfo.get("picture")
            first_name = userinfo.get("given_name")
            last_name = userinfo.get("family_name")
        else:
            raise ClientError(user_msg="User email not available or not verified by Google.")

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_email(db_session, users_email)

            if not user:
                raise NotAuthorizedError(user_msg="No user found for the given Google account.  User email must match the Google account email.")

            update_data = {}

            if not user.first_name and first_name:
                self.logger.debug("User '%s' first name not set in database.  Updating from google: %s", users_email, first_name)
                update_data["first_name"] = first_name

            if not user.last_name and last_name:
                self.logger.debug("User '%s' last name not set in database.  Updating from google: %s", users_email, last_name)
                update_data["last_name"] = last_name
            
            if not user.google_oidc_id and unique_id:
                self.logger.debug("User '%s' google OIDC Id not set in database.  Updating from google: %s", users_email, unique_id)
                update_data["google_oidc_id"] = unique_id

            if not user.profile_pic and picture:
                self.logger.debug("User '%s' profile pic url not set in database.  Updating from google: %s", users_email, picture)
                update_data["profile_pic"] = picture

            if update_data:
                self.logger.debug("Updating user account '%s' with missing data: %s", users_email, update_data)
                UsersDB.update(db_session, user.id, **update_data)

            # Begin user session by logging the user in
            login_user(AuthUser.from_user(user))

        # Send user back to homepage
        return redirect("/manage")
        
class Logout(BaseResource, ResourceMixinBase):
    @login_required
    def get(self):
        logout_user()
        return redirect("/login")

class Login(BaseResource, ResourceMixinBase):    
    def post(self):
        data = self.get_request_data()

        email = data.get("email")
        password = data.get("password")

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_email(db_session, email)

            if not user:
                raise NotAuthorizedError()

            if not user.password_hash:
                raise ClientError(user_msg="The user does not have a password set.  Please try logging in with google.")

            ph = PasswordHasher()
            try:
                if not ph.verify(user.password_hash, password):
                    raise NotAuthorizedError()
            except VerifyMismatchError:
                raise NotAuthorizedError()

            login_user(AuthUser.from_user(user))
        
        return True
        