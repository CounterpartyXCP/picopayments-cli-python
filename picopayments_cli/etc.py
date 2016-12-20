# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import json


# path and network settings
testnet = None
netcode = None
basedir = None
config_path = None
wallet_path = None
data_path = None


hub_url = None
hub_username = None
hub_password = None
hub_verify_ssl_cert = None


def load(basedir, testnet):

    # ensure basedir path exists
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    # update path and network settings
    wallet_file = "testnet.wif" if testnet else "mainnet.wif"
    config_file = "testnet.cfg" if testnet else "mainnet.cfg"
    data_file = "testnet.data" if testnet else "mainnet.data"
    globals().update({
        "basedir": basedir,
        "testnet": testnet,
        "netcode": "XTN" if testnet else "BTC",
        "wallet_path": os.path.join(basedir, wallet_file),
        "config_path": os.path.join(basedir, config_file),
        "data_path": os.path.join(basedir, data_file)
    })

    # load config
    if os.path.exists(config_path):
        with open(config_path, 'r') as infile:
            config = json.load(infile)

    # create config if it does not exist
    else:
        with open(config_path, 'w') as outfile:
            port = 15000 if testnet else 5000
            subdomain = "micro.test" if testnet else "micro"
            config = {
                "hub_url": "https://{subdomain}.storj.io:{port}/api/".format(
                    subdomain=subdomain, port=port
                ),
                "hub_username": None,
                "hub_password": None,
                "hub_verify_ssl_cert": True,
            }
            json.dump(config, outfile, indent=2, sort_keys=True)

    # update config settings
    globals().update(config)
