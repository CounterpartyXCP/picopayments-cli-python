# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
from . import util
from .rpc import API
from .mpc import Mpc


class Mph(Mpc):

    _SERIALIZABLE_ATTRS = [
        "asset",  # set once
        "handle",  # set once
        "channel_terms",  # set once
        "client_wif",  # set once
        "client_pubkey",  # set once
        "hub_pubkey",  # set once
        "secrets",  # append only
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
    def deserialize(cls, data, api_cls=API):
        """TODO doc string"""
        obj = cls(api_cls(**data["hub"]))
        for attr in obj._SERIALIZABLE_ATTRS:
            setattr(obj, attr, data[attr])
        return obj

    def serialize(self):
        """TODO doc string"""
        data = {
            "hub": {
                "url": self.api.url,
                "auth_wif": self.api.auth_wif,
                "username": self.api.username,
                "password": self.api.password,
                "verify_ssl_cert": self.api.verify_ssl_cert,
            }
        }
        for attr in self._SERIALIZABLE_ATTRS:
            data[attr] = getattr(self, attr)
        return data

    def is_connected(self):
        """Returns True if connected to a hub."""
        return bool(self.handle)

    def connect(self, quantity, expire_time=1024, asset="XCP",
                delay_time=2, own_url=None, dryrun=False):
        """TODO doc string"""

        assert(not self.is_connected())
        self.asset = asset
        self.client_wif = self.api.auth_wif
        self.own_url = own_url
        self.client_pubkey = util.wif2pubkey(self.client_wif)
        self.c2h_deposit_expire_time = expire_time
        self.c2h_deposit_quantity = quantity
        next_revoke_hash = self._create_initial_secrets()
        self._request_connection()
        self._validate_matches_terms()
        c2h_deposit_rawtx = self._make_deposit()
        h2c_deposit_script = self._exchange_deposit_scripts(next_revoke_hash)
        signed_rawtx = self.sign(c2h_deposit_rawtx, self.client_wif)
        c2h_deposit_txid = self.publish(signed_rawtx, dryrun=dryrun)
        self._set_initial_h2c_state(h2c_deposit_script)
        self._add_to_commits_requested(next_revoke_hash)
        self.payments_sent = []
        self.payments_received = []
        self.payments_queued = []
        self.c2h_commit_delay_time = delay_time
        return c2h_deposit_txid

    def micro_send(self, handle, quantity, token=None):
        """TODO doc string"""

        assert(self.is_connected())
        if token is None:
            token = util.b2h(os.urandom(32))
        self.payments_queued.append({
            "payee_handle": handle,
            "amount": quantity,
            "token": token
        })
        return token

    def get_status(self, clearance=6):
        assert(self.is_connected())
        asset = self.asset
        netcode = util.wif2netcode(self.client_wif)
        h2c_expired = self.api.mpc_deposit_expired(
            state=self.h2c_state, clearance=clearance
        )
        c2h_expired = self.api.mpc_deposit_expired(
            state=self.c2h_state, clearance=clearance
        )
        c2h_deposit_address = util.script2address(
            self.c2h_state["deposit_script"], netcode=netcode
        )
        c2h_deposit = self.get_balances(c2h_deposit_address, [asset])[asset]
        h2c_deposit_address = util.script2address(
            self.h2c_state["deposit_script"], netcode=netcode
        )
        h2c_deposit = self.get_balances(h2c_deposit_address, [asset])[asset]
        c2h_transferred = self.api.mpc_transferred_amount(state=self.c2h_state)
        h2c_transferred = self.api.mpc_transferred_amount(state=self.h2c_state)
        return {
            "asset": asset,
            "netcode": netcode,
            "c2h_expired": c2h_expired,
            "h2c_expired": h2c_expired,
            "balance": c2h_deposit + h2c_transferred - c2h_transferred,
            "c2h_deposit_quantity": c2h_deposit,
            "h2c_deposit_quantity": h2c_deposit,
            "c2h_transferred_quantity": c2h_transferred,
            "h2c_transferred_quantity": h2c_transferred,
        }

    def sync(self):
        """TODO doc string"""

        assert(self.is_connected())
        payments = self.payments_queued
        self.payments_queued = []

        # transfer payment funds (create commit/revokes)
        sync_fee = self.channel_terms["sync_fee"]
        quantity = sum([p["amount"] for p in payments]) + sync_fee
        result = self.full_duplex_transfer(
            self.client_wif, self.secrets.get, self.c2h_state,
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

    def close(self, dryrun=False):
        return self.finalize_commit(
            self._get_wif, self.h2c_state, dryrun=dryrun
        )

    def is_closed(self, clearance=6):
        c2h = self.c2h_state
        h2c = self.h2c_state
        return (
            self.api.mpc_deposit_expired(state=c2h, clearance=clearance) or
            self.api.mpc_deposit_expired(state=h2c, clearance=clearance) or
            self.api.mpc_get_published_commits(state=c2h) or
            self.api.mpc_get_published_commits(state=h2c)
        )

    def update(self, dryrun=False, clearance=6):
        txids = []

        # close channel if needed
        h2c_closed = self.api.mpc_get_published_commits(state=self.h2c_state)
        if self.is_closed(clearance=clearance) and not h2c_closed:
            txid = self.close(self, dryrun=dryrun)
            if txid:
                txids.append(txid)

        # recover funds if possible
        txids += self.full_duplex_recover_funds(
            self._get_wif, self.secrets.get, self.h2c_state,
            self.c2h_state, dryrun=dryrun
        )

        return txids

    def _get_wif(self, pubkey):
        return self.client_wif

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
