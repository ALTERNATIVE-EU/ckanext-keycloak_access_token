from __future__ import annotations

import logging


import ckan.logic
import ckan.logic.action
import ckan.logic.schema
import ckan.plugins as plugins
import ckan.lib.api_token as api_token
import ckanext.keycloak_access_token.db.access_token as db
import ckan.lib.dictization.model_dictize as model_dictize
import sqlite3
import psycopg2
import requests

from sqlite3 import Error

from ckan.common import _, request, config

log = logging.getLogger('ckan.logic')

ValidationError = ckan.logic.ValidationError
NotFound = ckan.logic.NotFound
_get_or_bust = ckan.logic.get_or_bust


def add_record_to_table(dbname, user, password, host, table, record):
    """
    Adds a record to a PostgreSQL table.

    :param dbname: Name of the database
    :param user: Database user
    :param password: Database password for the user
    :param host: Host where the database server is running
    :param table: Name of the table where the record will be added
    :param record: A tuple containing the record to be added
    """
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    
    try:
        # Create a new cursor
        cur = conn.cursor()
        
        # Generate the SQL query for inserting data
        # Assuming record is a tuple of values corresponding to the table columns
        placeholders = ', '.join(['%s'] * len(record))
        query = f"INSERT INTO {table} VALUES ({placeholders});"
        
        # Execute the SQL command
        cur.execute(query, record)
        
        # Commit the changes to the database
        conn.commit()
        
        # Close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

def access_token_revoke(context, data_dict):
    jti = data_dict.get(u'jti')
    if not jti:
        token = _get_or_bust(data_dict, u'token')
        decoders = plugins.PluginImplementations(plugins.IApiToken)
        for plugin in decoders:
            data = plugin.decode_api_token(token)
            if data:
                break
        else:
            data = api_token.decode(token)

        if data:
            jti = data.get(u'jti')

    add_record_to_table(
        config.get('ckanext.access_tokens.database_name'),
        config.get('ckanext.access_tokens.username'),
        config.get('ckanext.access_tokens.password'),
        config.get('ckanext.access_tokens.host'),
        config.get('ckanext.access_tokens.table'),
        (jti,)
    )
    
    # Refresh the tokens cache
    url = config.get('ckanext.access_tokens.url')
    headers = {
    'X-Refresh-Cache': 'true',
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 204:
        raise Exception('Failed to refresh tokens')
    
    model = context["model"]
    access_token_for_deletion = model.Session.query(db.AccessTokenTable).filter_by(id=jti)
    access_token_for_deletion.delete()
    model.Session.commit()