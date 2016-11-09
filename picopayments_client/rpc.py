# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import re
import time
import json
import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict
from six.moves.urllib.parse import urljoin
from . import auth


method_cumulative_calltime = defaultdict(float)


class JsonRpcCallFailed(Exception):

    def __init__(self, payload, response):
        msg = "Rpc call failed! {0} -> {1}".format(payload, response)
        super(JsonRpcCallFailed, self).__init__(msg)


def _jsonrpc_call(url, method, params={}, verify_ssl_cert=True,
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


def _auth_jsonrpc_call(url, method, params={}, verify_ssl_cert=True,
                       privkey=None, username=None, password=None):

    if privkey:
        params = auth.sign_json(params, privkey)

    result = _jsonrpc_call(url, method, params=params, username=username,
                           password=password, verify_ssl_cert=verify_ssl_cert)

    if privkey:
        auth.verify_json(result)

    return result


class JsonRpc(object):

    def __init__(self, url, privkey=None, verify_ssl_cert=True,
                 username=None, password=None):
        self.url = url
        self.privkey = privkey
        self.username = username
        self.password = password
        self.verify_ssl_cert = verify_ssl_cert

    def __getattribute__(self, name):
        props = ["url", "privkey", "verify_ssl_cert", "username", "password"]
        auth_methods = ["mph_request", "mph_deposit", "mph_sync", "test_auth"]

        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(**kwargs):
            privkey = self.privkey if name in auth_methods else None
            return _auth_jsonrpc_call(
                url=self.url,
                method=name,
                params=kwargs,
                privkey=privkey,
                verify_ssl_cert=self.verify_ssl_cert,
                username=self.username,
                password=self.password
            )
        return wrapper
