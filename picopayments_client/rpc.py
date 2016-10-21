# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import time
import json
import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict
from . import auth


method_call_time = defaultdict(float)


class RpcCallFailed(Exception):

    def __init__(self, payload, response):
        msg = "Rpc call failed! {0} -> {1}".format(payload, response)
        super(RpcCallFailed, self).__init__(msg)


def http_call(url, method, params={}, verify_ssl_cert=True,
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

    global method_call_time
    begin = time.time()
    response = requests.post(**kwargs).json()
    method_call_time[method] += (time.time() - begin)

    if "result" not in response:
        raise RpcCallFailed(payload, response)
    return response["result"]


def auth_http_call(url, method, params={},
                   verify_ssl_cert=True, auth_privkey=None,
                   username=None, password=None):

    if auth_privkey:
        params = auth.sign_json(params, auth_privkey)

    result = http_call(url, method, params=params,
                       username=username, password=password,
                       verify_ssl_cert=verify_ssl_cert)

    if auth_privkey:
        auth.verify_json(result)

    return result


class API(object):

    def __init__(self, url, auth_privkey=None, verify_ssl_cert=True,
                 username=None, password=None):
        self.url = url
        self.auth_privkey = auth_privkey
        self.username = username
        self.password = password
        self.verify_ssl_cert = verify_ssl_cert

    def __getattribute__(self, name):
        props = [
            "url", "auth_privkey", "verify_ssl_cert",
            "username", "password"
        ]
        auth_methods = ["mph_request", "mph_deposit", "mph_sync", "test_auth"]

        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(**kwargs):
            auth_privkey = self.auth_privkey if name in auth_methods else None
            return auth_http_call(
                url=self.url,
                method=name,
                params=kwargs,
                auth_privkey=auth_privkey,
                verify_ssl_cert=self.verify_ssl_cert,
                username=self.username,
                password=self.password)
        return wrapper
