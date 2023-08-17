import os
from json import loads
from os import environ, path
import logging
import logging.config
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

base_path = environ.get('TMP_PATH')


def generate_headers(token):
    """

    :param token:
    :return:
    """

    authorization = 'Bearer ' + token
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    return headers


def update_okta_token():  # pragma: no cover
    """

    :return:
    """

    url = 'https://dev-30456587.okta.com/oauth2/default/v1/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    data_dict = dict()
    data_dict['grant_type'] = 'client_credentials'
    data_dict['client_id'] = environ.get('OKTA_CLIENT_ID')
    data_dict['client_secret'] = environ.get('OKTA_CLIENT_SECRET')
    data_dict['scope'] = 'admin'
    post_return = requests.post(url, headers=headers, data=data_dict)
    logging.warning(post_return.text)
    response_dict = loads(post_return.text)
    token = response_dict['access_token']
    okta_file = base_path + 'okta_token'
    os.makedirs(base_path, exist_ok=True)
    with open(okta_file, 'w') as okta_fh:
        okta_fh.write("%s" % token)
    return token


def get_authentication_token():  # pragma: no cover
    okta_file = base_path + 'okta_token'
    token = ''
    if path.isfile(okta_file):
        one_day_ago = datetime.now() - relativedelta(days=1)
        file_time = datetime.fromtimestamp(path.getmtime(okta_file))
        if file_time > one_day_ago:
            with open(okta_file, 'r') as okta_fh:
                token = okta_fh.read().replace("\n", "")
        else:
            token = update_okta_token()
    else:
        token = update_okta_token()
    return token
