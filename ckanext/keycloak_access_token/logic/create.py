from __future__ import annotations
import datetime

import logging

import ckan.logic as logic
import ckan.lib.dictization
import ckan.logic.validators
import ckan.logic.action
import ckan.logic.schema
import ckan.lib.navl.dictization_functions
import ckan.lib.datapreview
import ckan.lib.api_token as api_token
import jwt
import requests
import ckan.model
import ckanext.keycloak_access_token.db.access_token as db
from ckan.common import _, request, config

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

    validated_data_dict, errors = _validate(data_dict, schema, context)

    if errors:
        raise ValidationError(errors)

    # Get the token from the cookies

    token_obj = exchange_token(
        keycloak_url=config.get('ckanext.keycloak.server_url'),
        client_id=config.get("ckanext.keycloak.client_id"),
        client_secret=config.get("ckanext.keycloak.client_secret_key"),
        original_token=request.cookies.get("jwt_access_token"),
        realm_name=config.get("ckanext.keycloak.realm"),
        audience=config.get('ckanext.keycloak.ai_ml_api_client_id'),
    )

    # parse the token
    parsed_token = jwt.decode(str(token_obj).encode("utf-8"), verify=False)

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
