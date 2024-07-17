import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.keycloak_access_token.blueprint as blueprint
import ckanext.keycloak_access_token.logic.create as create
import ckanext.keycloak_access_token.logic.delete as delete
from sqlalchemy import engine_from_config

from ckanext.keycloak_access_token.auth.create import access_token_create

from ckanext.keycloak_access_token.db.access_token import Base, AccessTokenTable


class KeycloakAccessTokenPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'access_token_create': access_token_create,
        }

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        
        engine = engine_from_config(config_, 'sqlalchemy.')
        Base.metadata.create_all(engine)

    # IBlueprint
    def get_blueprint(self):
        return blueprint.keycloak_access_token

    # IActions
    def get_actions(self):
        return {
            'access_token_create': create.access_token_create,
            'access_token_revoke': delete.access_token_revoke,
        }