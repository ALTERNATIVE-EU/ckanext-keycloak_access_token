# encoding: utf-8

import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
from ckan import authz
import ckanext.keycloak_access_token.logic.get as get_token
import dominate.tags as dom_tags
from six import ensure_str
from ckan.common import (
    _, g, request
)

import ckan.lib.navl.dictization_functions as dictization_functions

from flask import Blueprint

keycloak_access_token = Blueprint(u'keycloak_access_token', __name__)

def _extra_template_variables(context, data_dict):
    is_sysadmin = authz.is_sysadmin(g.user)
    try:
        user_dict = logic.get_action(u'user_show')(context, data_dict)
    except logic.NotFound:
        base.abort(404, _(u'User not found'))
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    is_myself = user_dict[u'name'] == g.user
    about_formatted = h.render_markdown(user_dict[u'about'])
    extra = {
        u'is_sysadmin': is_sysadmin,
        u'user_dict': user_dict,
        u'is_myself': is_myself,
        u'about_formatted': about_formatted
    }
    return extra

def get(id, data=None, errors=None, error_summary=None):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True,
        u'include_plugin_extras': True
    }
    try:
        tokens = get_token.api_token_list(context, {u'user': id})
    except logic.NotAuthorized:
        base.abort(403, _(u'Unauthorized to view API tokens.'))

    data_dict = {
        u'id': id,
        u'user_obj': g.userobj,
        u'include_datasets': True,
        u'include_num_followers': True
    }

    extra_vars = _extra_template_variables(context, data_dict)
    if extra_vars is None:
        return h.redirect_to(u'user.login')
    extra_vars[u'tokens'] = tokens
    extra_vars.update({
        u'data': data,
        u'errors': errors,
        u'error_summary': error_summary
    })
    return base.render(u'user/keycloak_access_token.html', extra_vars)

def post(id):
    data_dict = logic.clean_dict(
        dictization_functions.unflatten(
            logic.tuplize_dict(logic.parse_params(request.form))))

    data_dict[u'user'] = id
    try:
        token = logic.get_action(u'access_token_create')(
            {},
            data_dict
        )[u'token']
    except logic.NotAuthorized:
        base.abort(403, _(u'Unauthorized to create API tokens.'))
    except logic.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        return get(id, data_dict, errors, error_summary)
    except Exception as e:
        base.abort(403, _(u'Error creating AI/ML API token: %s') % str(e))

    copy_btn = dom_tags.button(dom_tags.i(u'', {
        u'class': u'fa fa-copy'
    }), {
        u'type': u'button',
        u'class': u'btn btn-default btn-xs',
        u'data-module': u'copy-into-buffer',
        u'data-module-copy-value': ensure_str(token)
    })
    h.flash_success(
        _(
            u"API Token created: <code style=\"word-break:break-all;\">"
            u"{token}</code> {copy}<br>"
            u"Make sure to copy it now, "
            u"you won't be able to see it again!"
        ).format(token=ensure_str(token), copy=copy_btn),
        True
    )
    return h.redirect_to(u'keycloak_access_token.get', id=id)

def access_token_revoke(id: str, jti: str):
    try:
        logic.get_action(u'access_token_revoke')({}, {u'jti': jti})
    except logic.NotAuthorized:
        base.abort(403, _(u'Unauthorized to revoke API tokens.'))
    except Exception as e:
        base.abort(500, _(u'Error while revoking API token: {error}').format(error=str(e)))
    return h.redirect_to(u'keycloak_access_token.get', id=id)

keycloak_access_token.add_url_rule(
    u'/user/keycloak_access_token/<string:id>', view_func=get
)

keycloak_access_token.add_url_rule(
    u'/user/keycloak_access_token/<string:id>', view_func=post, methods=[u'POST']
)

keycloak_access_token.add_url_rule(
    u'/<id>/access-tokens/<jti>/revoke', view_func=access_token_revoke,
    methods=(u'POST',)
)