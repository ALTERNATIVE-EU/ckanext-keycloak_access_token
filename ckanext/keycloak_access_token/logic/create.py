from __future__ import annotations

import datetime
import logging

import ckan.lib.api_token as api_token
import ckan.lib.datapreview
import ckan.lib.dictization
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.logic.action
import ckan.logic.schema
import ckan.logic.validators
import ckan.model
import ckan.plugins.toolkit as toolkit
import ckanext.keycloak_access_token.db.access_token as db
import requests

from ckan.common import _, config, request
from jose import jwt

log = logging.getLogger(__name__)

_validate = ckan.lib.navl.dictization_functions.validate
_check_access = logic.check_access
ValidationError = logic.ValidationError
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust


def exchange_token(
    keycloak_url,
    client_id,
    client_secret,
    original_token,
    realm_name,
    audience,
    scopes="offline_access",
    ):
    """
    Exchange a token for a different token using Keycloak's Token Exchange feature.

    :param keycloak_url: The base URL of your Keycloak server.
    :param client_id: The client ID for the client you are exchanging the token to.
    :param client_secret: The client secret for the client.
    :param original_token: The original token you want to exchange.
    :param realm_name: The name of the Keycloak realm.
    :param subject_token_type: The type of the original token being exchanged.
    :param requested_token_type: The type of the token you are requesting.
    :return: The new exchanged token or None if exchange failed.
    """
    token_endpoint = (
        f"{keycloak_url}/realms/{realm_name}/protocol/openid-connect/token"
    )
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": original_token,
        "audience": audience,
        "scope": scopes,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_endpoint, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Token exchange failed: {response.text}")
        
        if response.json().get("error") and response.json().get("error") == "invalid_token":
            raise Exception(f"Session Expired")
        else:
            raise Exception('Failed to exchange token')

def access_token_create(context, data_dict):
    model = context["model"]
    user, name = _get_or_bust(data_dict, ["user", "name"])
    
    user_obj = model.User.get(data_dict["user"])
    user_id = user_obj.id if user_obj else None

    if model.User.get(user) is None:
        raise NotFound("User not found")

    _check_access("access_token_create", context, data_dict)

    schema = context.get(u'schema')
    if not schema:
        schema = api_token.get_schema()

    _, errors = _validate(data_dict, schema, context)

    if errors:
        raise ValidationError(errors)

    # Get the token
    session_id = toolkit.request.cookies.get("session_id")
    if not session_id:
        raise Exception(u"Session ID missing")
    
    get_user_session = toolkit.get_action("get_user_session")
    data_dict = logic.clean_dict(
        dictization_functions.unflatten(
            logic.tuplize_dict(logic.parse_params(request.form))))

    data_dict[u'session_id'] = session_id
    user_session = get_user_session(context, data_dict)[u'user_session']
    if not user_session:
        return None
    
    if user_session and user_session.jwttokens:
        access_token = user_session.jwttokens.access_token
        
    if not access_token:
        raise Exception(u"Access token missing")

    token_obj = exchange_token(
        keycloak_url=config.get('ckanext.keycloak.server_url'),
        client_id=config.get("ckanext.keycloak.client_id"),
        client_secret=config.get("ckanext.keycloak.client_secret_key"),
        original_token=access_token,
        realm_name=config.get("ckanext.keycloak.realm"),
        audience=config.get('ckanext.keycloak.ai_ml_api_client_id'),
    )

    server_url = config.get("ckanext.keycloak.server_url")
    realm = config.get("ckanext.keycloak.realm")
    
    secret_key = fetch_secret_key(f"{server_url}/realms/{realm}/protocol/openid-connect/certs")

    parsed_token = jwt.decode(token_obj, secret_key, options={"verify_aud": False})

    if token_obj is None:
        raise ValidationError("Token exchange failed")

    token_record = db.AccessTokenTable(
        id=parsed_token.get("jti"),
        name=name,
        user_id=user_id,
        created_at=datetime.datetime.utcfromtimestamp(parsed_token.get("iat")),
        expires_at=datetime.datetime.utcfromtimestamp(parsed_token.get("exp")),
        last_access=None,
        plugin_extras={},
    )

    if token_record:
        model.Session.add(token_record)
        model.Session.commit()

    result = api_token.add_extra({"token": token_obj})

    return result

def fetch_secret_key(url):
    response = requests.get(url, verify=True)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch secret key")
    
