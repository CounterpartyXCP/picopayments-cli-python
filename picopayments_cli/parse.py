# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import re
from pycoin.key import validate
from micropayment_core.scripts import MAX_SEQUENCE


HOST_REGEX = re.compile(
    r'^localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',  # ...or ip
    re.IGNORECASE
)


def asset(value):
    if value is None:
        return None
    return str(value)


def address(value):
    if value is None:
        return None
    value = str(value)
    valid = validate.is_address_valid(value, allowable_netcodes=["XTN", "BTC"])
    assert valid, "{} is not a bitcoin address!".format(value)
    return value


def unsigned(value):
    if value is None:
        return None
    value = int(value)
    assert value >= 0, "{0} is not an unsigned integer!".format(value)
    return value


def satoshis(value):
    if value is None:
        return None
    value = unsigned(value)
    valid = 2100000000000000 >= value >= 0
    assert valid, "{} not a valid satoshis amount!".format(value)
    return value


def sequence(value):
    if value is None:
        return None
    value = unsigned(value)
    valid = MAX_SEQUENCE >= value >= 0
    assert valid, "{} not a valid sequence value!".format(value)
    return value


def hexdata(value):
    if value is None:
        return None
    value = str(value)
    valid = re.match("^[a-f0-9]+$", value)
    assert valid, "{} not a valid hex value!".format(value)
    return value


def hex256(value):
    if value is None:
        return None
    value = hexdata(value)
    valid = len(value) == (256 / 4)  # 256 bits of hex data
    assert valid, "{} not 256 bits of hex data!".format(value)
    return value


def txid(value):
    return hex256(value)


def handle(value):
    return hex256(value)


def token(value):
    if value is None:
        return None
    return hexdata(value)


def host(value):
    if value is None:
        return None
    value = str(value)
    valid = re.match(HOST_REGEX, value)
    assert valid, "{} not a valid hostname!".format(value)
    return value


def port(value):
    if value is None:
        return None
    value = unsigned(value)
    valid = 2 ** 16 > value > 0
    assert valid, "{} not a valid port".format(value)
    return value
