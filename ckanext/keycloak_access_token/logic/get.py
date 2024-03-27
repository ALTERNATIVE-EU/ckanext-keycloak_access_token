from __future__ import annotations

import logging

import ckanext.keycloak_access_token.db.access_token as db

import ckan
import ckan.lib.dictization
import ckan.logic as logic
import ckan.logic.action
import ckan.logic.schema
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.navl.dictization_functions
import ckan.model as model


from ckan.common import _

log = logging.getLogger('ckan.logic')

# Define some shortcuts
# Ensure they are module-private so that they don't get loaded as available
# actions in the action API.
_check_access = logic.check_access
NotFound = logic.NotFound
ValidationError = logic.ValidationError

def api_token_list(context, data_dict):

    # Support "user" for backwards compatibility
    id_or_name = data_dict.get("user_id", data_dict.get("user"))
    if not id_or_name:
        raise ValidationError({"user_id": ["Missing value"]})

    _check_access(u'api_token_list', context, data_dict)
    user = model.User.get(id_or_name)
    if user is None:
        raise NotFound("User not found")
    tokens = model.Session.query(db.AccessTokenTable).filter_by(user_id=user.id)
    print("Tokens: ", model_dictize.api_token_list_dictize(tokens, context))
    return model_dictize.api_token_list_dictize(tokens, context)