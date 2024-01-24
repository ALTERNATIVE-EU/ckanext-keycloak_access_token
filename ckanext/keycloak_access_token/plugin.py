import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.keycloak_access_token.blueprint as blueprint


class KeycloakAccessTokenPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    # IBlueprint
    def get_blueprint(self):
        return blueprint.keycloak_access_token
