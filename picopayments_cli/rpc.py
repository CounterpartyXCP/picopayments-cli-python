# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import time
import json
import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict
from . import auth


method_cumulative_calltime = defaultdict(float)


class JsonRpcCallFailed(Exception):

    def __init__(self, payload, response):
        msg = "Rpc call failed! {0} -> {1}".format(payload, response)
        super(JsonRpcCallFailed, self).__init__(msg)


def jsonrpc_call(url, method, params={}, verify_ssl_cert=True,
                 username=None, password=None):
    payload = {"method": method, "params": params, "jsonrpc": "2.0", "id": 0}
    kwargs = {
        "url": url,
        "headers": {'content-type': 'application/json'},
        "data": json.dumps(payload),
        "verify": verify_ssl_cert,
    }
    if username and password:
        kwargs["auth"] = HTTPBasicAuth(username, password)

    global method_cumulative_calltime
    begin = time.time()
    response = requests.post(**kwargs).json()
    method_cumulative_calltime[method] += (time.time() - begin)

    if "result" not in response:
        raise JsonRpcCallFailed(payload, response)
    return response["result"]


def auth_jsonrpc_call(url, method, params={}, verify_ssl_cert=True,
                      auth_wif=None, username=None, password=None):

    if auth_wif:
        params = auth.sign_json(params, auth_wif)

    result = jsonrpc_call(url, method, params=params, username=username,
                          password=password, verify_ssl_cert=verify_ssl_cert)

    if auth_wif:
        auth.verify_json(result)

    return result


class JsonRpc(object):

    def __init__(self, url, auth_wif=None, verify_ssl_cert=True,
                 username=None, password=None):
        self.url = url
        self.auth_wif = auth_wif
        self.username = username
        self.password = password
        self.verify_ssl_cert = verify_ssl_cert

    def __getattribute__(self, name):
        props = ["url", "auth_wif", "verify_ssl_cert", "username", "password"]
        # FIXME only allow test_auth in unit tests
        auth_methods = [
            "mph_request", "mph_deposit", "mph_sync", "mph_close"
        ]

        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(**kwargs):
            auth_wif = self.auth_wif if name in auth_methods else None
            return auth_jsonrpc_call(
                url=self.url,
                method=name,
                params=kwargs,
                auth_wif=auth_wif,
                verify_ssl_cert=self.verify_ssl_cert,
                username=self.username,
                password=self.password
            )
        return wrapper
