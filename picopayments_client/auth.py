# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import copy
import json
import pyelliptic
from . import util


class AuthPubkeyMissmatch(Exception):

    def __init__(self, expected, found):
        msg = "Given pubkey {0} does not match signing pubkey {1}!".format(
            found, expected
        )
        super(AuthPubkeyMissmatch, self).__init__(msg)


class InvalidAuthSignature(Exception):

    def __init__(self, pubkey, signature, data):
        msg = "Invalid auth signature for pubkey {0}, signature {1}, data {2}"
        super(InvalidAuthSignature, self).__init__(
            msg.format(pubkey, signature, data)
        )


def sign(wif, data):
    privkey = util.wif2privkey(wif)
    pubkey = util.wif2pubkey(wif)
    uncompressed_sec = util.decode_pubkey(pubkey)
    ecc = pyelliptic.ECC(
        curve="secp256k1", pubkey=uncompressed_sec, privkey=privkey
    )
    return util.b2h(ecc.sign(data))


def verify(pubkey, signature, data):
    uncompressed_sec = util.decode_pubkey(pubkey)
    ecc = pyelliptic.ECC(curve="secp256k1", pubkey=uncompressed_sec)
    if not ecc.verify(util.h2b(signature), data):
        raise InvalidAuthSignature(pubkey, signature, data)


def sign_json(json_data, wif):

    # add pubkey to json data if needed
    pubkey = util.wif2pubkey(wif)
    if "pubkey" in json_data and not json_data["pubkey"] == pubkey:
        raise AuthPubkeyMissmatch(pubkey, json_data["pubkey"])
    else:
        json_data["pubkey"] = pubkey

    # sign serialized data (keys must be ordered!)
    data = json.dumps(json_data, sort_keys=True)
    signature = sign(wif, data)

    # add signature to json data
    json_data["signature"] = signature

    return json_data


def verify_json(json_data):
    json_data = copy.deepcopy(json_data)
    pubkey = json_data["pubkey"]
    signature = json_data.pop("signature")
    data = json.dumps(json_data, sort_keys=True)
    verify(pubkey, signature, data)
