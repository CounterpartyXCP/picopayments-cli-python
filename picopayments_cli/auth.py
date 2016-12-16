# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import copy
import json
from micropayment_core import keys


class AuthPubkeyMissmatch(Exception):

    def __init__(self, expected, found):
        msg = "Given pubkey {0} does not match signing pubkey {1}!".format(
            found, expected
        )
        super(AuthPubkeyMissmatch, self).__init__(msg)


def sign_json(json_data, auth_wif):
    privkey = keys.wif_to_privkey(auth_wif)

    # add pubkey to json data if needed
    pubkey = keys.pubkey_from_privkey(privkey)
    if "pubkey" in json_data and not json_data["pubkey"] == pubkey:
        raise AuthPubkeyMissmatch(pubkey, json_data["pubkey"])
    else:
        json_data["pubkey"] = pubkey

    # sign serialized data (keys must be ordered!)
    data = json.dumps(json_data, sort_keys=True)
    signature = keys.sign_sha256(privkey, data.encode("utf-8"))

    # add signature to json data
    json_data["signature"] = signature

    return json_data


def verify_json(json_data):
    json_data = copy.deepcopy(json_data)
    pubkey = json_data["pubkey"]
    signature = json_data.pop("signature")
    data = json.dumps(json_data, sort_keys=True)
    return keys.verify_sha256(pubkey, signature, data.encode("utf-8"))
