# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import time
from micropayment_core import util
from micropayment_core import keys
from micropayment_core import scripts
from .mpc import Mpc


class Mph(Mpc):

    _SERIALIZABLE_ATTRS = [
        "asset",  # set once
        "handle",  # set once
        "channel_terms",  # set once
        "client_pubkey",  # set once
        "hub_pubkey",  # set once
        "secrets",  # FIXME save elsewhere?
        "c2h_state",  # mutable
        "c2h_spend_secret_hash",  # set once
        "c2h_commit_delay_time",  # set once
        "c2h_next_revoke_secret_hash",  # mutable
        "c2h_deposit_expire_time",  # set once
        "c2h_deposit_quantity",  # set once
        "h2c_state",  # set once
        "payments_sent",
        "payments_received",
        "payments_queued",
    ]

    def __init__(self, *args, **kwargs):
        super(Mph, self).__init__(*args, **kwargs)
        for attr in self._SERIALIZABLE_ATTRS:
            setattr(self, attr, None)

    @classmethod
    def deserialize(cls, api, data):
        """TODO doc string"""
        obj = cls(api)
        for attr in obj._SERIALIZABLE_ATTRS:
            setattr(obj, attr, data[attr])
        return obj

    def serialize(self):
        """TODO doc string"""
        data = {}
        for attr in self._SERIALIZABLE_ATTRS:
            data[attr] = getattr(self, attr)
        return data

    def connect(self, quantity, expire_time=1024, asset="XCP",
                delay_time=2, own_url=None):
        """TODO doc string"""

        self.asset = asset
        self.own_url = own_url
        self.closed = False
        self.client_pubkey = keys.pubkey_from_wif(self.api.auth_wif)
        self.c2h_deposit_expire_time = expire_time
        self.c2h_deposit_quantity = quantity
        next_revoke_hash = self._create_initial_secrets()
        self._request_connection()
        self._validate_matches_terms()
        c2h_deposit_rawtx = self._make_deposit()
        h2c_deposit_script = self._exchange_deposit_scripts(next_revoke_hash)
        signed_rawtx = self.sign(c2h_deposit_rawtx, self.api.auth_wif)
        c2h_deposit_txid = self.publish(signed_rawtx)
        self._set_initial_h2c_state(h2c_deposit_script)
        self._add_to_commits_requested(next_revoke_hash)
        self.payments_sent = []
        self.payments_received = []
        self.payments_queued = []
        self.c2h_commit_delay_time = delay_time
        return c2h_deposit_txid

    def micro_send(self, handle, quantity, token=None):
        """TODO doc string"""

        if token is None:
            token = util.b2h(os.urandom(32))
        self.payments_queued.append({
            "payee_handle": handle,
            "amount": quantity,
            "token": token
        })
        return token

    def get_status(self, clearance=6):
        netcode = keys.netcode_from_wif(self.api.auth_wif)
        return self.full_duplex_channel_status(
            self.handle, netcode, self.c2h_state,
            self.h2c_state, self.secrets.get, clearance=clearance
        )

    def sync(self):
        """TODO doc string"""

        payments = self.payments_queued
        self.payments_queued = []

        # transfer payment funds (create commit/revokes)
        sync_fee = self.channel_terms["sync_fee"]
        quantity = sum([p["amount"] for p in payments]) + sync_fee
        result = self.full_duplex_transfer(
            self.api.auth_wif, self.secrets.get, self.c2h_state,
            self.h2c_state, quantity, self.c2h_next_revoke_secret_hash,
            self.c2h_commit_delay_time
        )
        commit = result["commit"]
        revokes = result["revokes"]
        self.h2c_state = result["recv_state"]
        self.c2h_state = result["send_state"]

        # create next revoke secret for h2c channel
        h2c_next_revoke_secret_hash = self._gen_secret()
        self._add_to_commits_requested(h2c_next_revoke_secret_hash)

        # sync with hub
        result = self.api.mph_sync(
            next_revoke_secret_hash=h2c_next_revoke_secret_hash,
            handle=self.handle, sends=payments, commit=commit, revokes=revokes
        )
        h2c_commit = result["commit"]
        c2h_revokes = result["revokes"]
        receive_payments = result["receive"]
        self.c2h_next_revoke_secret_hash = result["next_revoke_secret_hash"]
        self._update_payments(payments, receive_payments)

        # add commit to h2c channel
        if h2c_commit:
            self.h2c_state = self.api.mpc_add_commit(
                state=self.h2c_state,
                commit_rawtx=h2c_commit["rawtx"],
                commit_script=h2c_commit["script"]
            )

        # add c2h revokes to channel
        if c2h_revokes:
            self.c2h_state = self.api.mpc_revoke_all(
                state=self.c2h_state, secrets=c2h_revokes
            )

        return receive_payments

    def _update_payments(self, payments_sent, payments_received):
        for payment in payments_sent:
            self.payments_sent.append({
                "handle": payment["payee_handle"],
                "amount": payment["amount"],
                "token": payment["token"],
                "timestamp": time.time(),
            })
        for payment in payments_received:
            self.payments_received.append({
                "handle": payment["payer_handle"],
                "amount": payment["amount"],
                "token": payment["token"],
                "timestamp": time.time(),
            })

    def close(self):
        commit_txid = self.finalize_commit(self._get_wif, self.h2c_state)

        # get h2c spend secret if no commits for channel
        h2c_spend_secret = None
        if len(self.h2c_state["commits_active"]) == 0:
            deposit_script = self.h2c_state["deposit_script"]
            spend_hash = scripts.get_deposit_spend_secret_hash(deposit_script)
            h2c_spend_secret = self.secrets[spend_hash]

        # tell hub to close the channel
        result = self.api.mph_close(handle=self.handle,
                                    spend_secret=h2c_spend_secret)

        # remember c2h spend secret if given
        c2h_spend_secret = result["spend_secret"]
        if c2h_spend_secret:
            secret_hash = util.hash160hex(c2h_spend_secret)
            self.secrets[secret_hash] = c2h_spend_secret

        return commit_txid

    def is_closed(self, clearance=6):
        c2h = self.c2h_state
        h2c = self.h2c_state
        return (
            self.api.mpc_deposit_ttl(state=c2h, clearance=clearance) == 0 or
            self.api.mpc_deposit_ttl(state=h2c, clearance=clearance) == 0 or
            self.api.mpc_published_commits(state=c2h) or
            self.api.mpc_published_commits(state=h2c)
        )

    def update(self, clearance=6):
        txids = []

        # close channel if needed
        h2c_closed = self.api.mpc_published_commits(state=self.h2c_state)
        if self.is_closed(clearance=clearance) and not h2c_closed:
            txid = self.close()
            if txid:
                txids.append(txid)

        # recover funds if possible
        txids += self.full_duplex_recover_funds(
            self._get_wif, self.secrets.get, self.h2c_state, self.c2h_state
        )

        return txids

    def _get_wif(self, pubkey):
        return self.api.auth_wif

    def _add_to_commits_requested(self, secret_hash):
        # emulates mpc_request_commit api call
        self.h2c_state["commits_requested"].append(secret_hash)

    def _gen_secret(self):
        secret_value = util.b2h(os.urandom(32))
        secret_hash = util.hash160hex(secret_value)
        self.secrets[secret_hash] = secret_value
        return secret_hash

    def _create_initial_secrets(self):
        self.secrets = {}
        self.h2c_spend_secret_hash = self._gen_secret()
        return self._gen_secret()

    def _request_connection(self):
        result = self.api.mph_request(
            asset=self.asset, url=self.own_url,
            spend_secret_hash=self.h2c_spend_secret_hash
        )
        self.handle = result["handle"]
        self.channel_terms = result["channel_terms"]
        self.hub_pubkey = result["pubkey"]
        self.c2h_spend_secret_hash = result["spend_secret_hash"]

    def _exchange_deposit_scripts(self, h2c_next_revoke_secret_hash):
        result = self.api.mph_deposit(
            handle=self.handle, asset=self.asset,
            deposit_script=self.c2h_state["deposit_script"],
            next_revoke_secret_hash=h2c_next_revoke_secret_hash
        )
        h2c_deposit_script = result["deposit_script"]
        self.c2h_next_revoke_secret_hash = result["next_revoke_secret_hash"]
        return h2c_deposit_script

    def _make_deposit(self):
        result = self.api.mpc_make_deposit(
            asset=self.asset,
            payer_pubkey=self.client_pubkey,
            payee_pubkey=self.hub_pubkey,
            spend_secret_hash=self.c2h_spend_secret_hash,
            expire_time=self.c2h_deposit_expire_time,
            quantity=self.c2h_deposit_quantity
        )
        self.c2h_state = result["state"]
        return result["topublish"]

    def _validate_matches_terms(self):
        expire_max = self.channel_terms["expire_max"]
        deposit_max = self.channel_terms["deposit_max"]
        expire_time = self.c2h_deposit_expire_time
        quantity = self.c2h_deposit_quantity
        assert(expire_max == 0 or expire_time <= expire_max)
        assert(deposit_max == 0 or quantity <= deposit_max)

    def _set_initial_h2c_state(self, h2c_deposit_script):
        self.h2c_state = {
            "asset": self.asset,
            "deposit_script": h2c_deposit_script,
            "commits_requested": [],
            "commits_active": [],
            "commits_revoked": [],
        }
