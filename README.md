# ckanext-keycloak_access_token

CKAN extension that adds additional fields to dataset metadata, such as size and experiment info.

## Setup

1. Install <a href="https://docs.ckan.org/en/2.9/extensions/tutorial.html#installing-ckan" target="_blank">CKAN</a>

2. Clone the repository in the `src` dir (usually located in `/usr/lib/ckan/default/src`)
    ```
    cd /usr/lib/ckan/default/src
    git clone https://github.com/ALTERNATIVE-EU/ckanext-keycloak_access_token.git
    ```

3. Build the extension
    ```
    . /usr/lib/ckan/default/bin/activate
    cd /usr/lib/ckan/default/src/ckanext-keycloak_access_token
    sudo python3 setup.py develop
    ```

4. Add the extension to your list of plugins in the ckan config file (usually `/etc/ckan/default/ckan.ini`)
   ```
   ckan.plugins = stats text_view recline_view keycloak_access_token
   ```

5. Start CKAN
   ```
   . /usr/lib/ckan/default/bin/activate
   sudo ckan -c /etc/ckan/default/ckan.ini run
   ```