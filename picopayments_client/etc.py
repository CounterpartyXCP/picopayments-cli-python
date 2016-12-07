# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os


basedir = None
testnet = None
hub_url = None
hub_username = None
hub_password = None
hub_verify_ssl_cert = None
regular_dust_size = None
fee_per_kb = None


def load(basedir, testnet):

    # ensure basedir path exists
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    saved = {}  # FIXME load and create default if none exists
    default_hub_port = 15000 if testnet else 5000
    default_hub_url = "https://127.0.0.1:{0}/api/".format(default_hub_port)
    globals().update({
        "basedir": basedir,
        "testnet": testnet,
        "fee_per_kb": saved.get("fee_per_kb", 50000),
        "regular_dust_size": saved.get("regular_dust_size", 5430),
        "hub_url": saved.get("hub_url", default_hub_url),
        "hub_username": saved.get("hub_username", None),
        "hub_password": saved.get("hub_password", None),
        "hub_verify_ssl_cert": saved.get("hub_verify_ssl_cert", False),
    })
