# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import time
import json
import requests
import threading
from requests.auth import HTTPBasicAuth
from collections import defaultdict
import http.client
import socket
from future.moves.urllib.error import HTTPError, URLError
from . import auth


REQUEST_RETRY_LIMIT = 2  # only retries when network hickup occurs
method_cumulative_calltime = defaultdict(float)


class JsonRpcCallFailed(Exception):

    def __init__(self, payload, response):
        msg = "Rpc call failed! {0} -> {1}".format(payload, response)
        super(JsonRpcCallFailed, self).__init__(msg)


def _call(method, **kwargs):
    global method_cumulative_calltime
    error = None
    begin = time.time()
    success = False
    requests_made = 0
    while not success and requests_made < REQUEST_RETRY_LIMIT:
        try:
            requests_made += 1
            response = requests.post(**kwargs).json()
            success = True
        except HTTPError as e:
            error = e
        except http.client.HTTPException as e:
            error = e
        except URLError as e:
            error = e
        except socket.error as e:
            error = e
    if not success:
        raise Exception("Request {0} failed: {1}".format(method, str(error)))
    method_cumulative_calltime[method] += (time.time() - begin)
    return response


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

    response = _call(method, **kwargs)

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
        auth_methods = ["mph_request", "mph_deposit", "mph_sync", "mph_close"]

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


def _not_so_parallel_execute(jobs):
    """ Execute jobs in parallel using threads.

    Args:
        jobs: [{"func": REQUIRED, "args": (), "kwargs": {}, "name": REQUIRED}]

    Returns:
        Dict of job results {name: result}
    """
    results = {}
    for job in jobs:
        args = job.get("args", ())
        kwargs = job.get("kwargs", {})
        name = job["name"]
        result = job["func"](*args, **kwargs)
        results[name] = result
    return results


def parallel_execute(jobs):
    """ Execute jobs in parallel using threads.

    Args:
        jobs: [{"func": REQUIRED, "args": (), "kwargs": {}, "name": REQUIRED}]

    Returns:
        Dict of job results {name: result}
    """
    results = {}
    threads = []
    for job in jobs:
        def exec_job():
            args = job.get("args", ())
            kwargs = job.get("kwargs", {})
            name = job["name"]
            result = job["func"](*args, **kwargs)
            results[name] = result
        thread = threading.Thread(target=exec_job)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return results
