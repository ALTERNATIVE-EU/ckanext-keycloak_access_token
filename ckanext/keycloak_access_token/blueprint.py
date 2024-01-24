# encoding: utf-8

import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
from ckan import authz
from ckan.common import _,  g

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
        tokens = logic.get_action(u'api_token_list')(
            context, {u'user': id}
        )
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


keycloak_access_token.add_url_rule(
    u'/user/keycloak_access_token/<string:id>', view_func=get
)
