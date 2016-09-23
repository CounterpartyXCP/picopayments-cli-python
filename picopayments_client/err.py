# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


class InvalidScript(Exception):

    def __init__(self, x):
        msg = "Invalid script: '{0}'"
        super(InvalidScript, self).__init__(msg.format(x))


class InvalidPayerSignature(Exception):

    def __init__(self):
        msg = "Invalid or missing payer signature!"
        super(InvalidPayerSignature, self).__init__(msg)


class InvalidSequenceValue(Exception):

    def __init__(self, x):
        msg = "Invalid sequence value: {0}"
        super(InvalidSequenceValue, self).__init__(msg.format(x))


class RpcCallFailed(Exception):

    def __init__(self, payload, response):
        msg = "Rpc call failed! {0} -> {1}".format(payload, response)
        super(RpcCallFailed, self).__init__(msg)


class AuthPubkeyMissmatch(Exception):

    def __init__(self, expected, found):
        msg = "Given pubkey {0} does not match signing pubkey {1}!".format(
            found, expected
        )
        super(AuthPubkeyMissmatch, self).__init__(msg)


class InvalidSignature(Exception):

    def __init__(self, pubkey, signature, data):
        msg = "Invalid signature for pubkey {0}, signature {1}, data {2}"
        super(InvalidSignature, self).__init__(
            msg.format(pubkey, signature, data)
        )
