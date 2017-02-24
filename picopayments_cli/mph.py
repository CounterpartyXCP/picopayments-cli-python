# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import time
import copy
from micropayment_core import util
from micropayment_core import keys
from micropayment_core import scripts
from .mpc import Mpc, history_add_entry


class Mph(Mpc):

    _SERIALIZABLE_ATTRS = [
        "asset",  # set once
        "handle",  # set once
        "channel_terms",  # set once
        "client_pubkey",  # set once
        "hub_pubkey",  # set once
        "secrets",  # TODO save elsewhere?
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

    def _history_add_published_c2h_deposit(self, rawtx):
        self._history_add_rawtx(rawtx, "publish_c2h_deposit_tx")

    def _history_add_published_h2c_commit(self, rawtx):
        self._history_add_rawtx(rawtx, "publish_h2c_commit_tx",
                                wallet_tx=False)

    def _history_add_update_rawtxs(self, rawtxs):
        for txid, rawtx in rawtxs["payout"].items():
            self._history_add_rawtx(rawtx, "publish_h2c_payout_tx")
        for txid, rawtx in rawtxs["revoke"].items():
            self._history_add_rawtx(rawtx, "publish_c2h_revoke_tx")
        for txid, rawtx in rawtxs["change"].items():
            self._history_add_rawtx(rawtx, "publish_c2h_change_tx")
        for txid, rawtx in rawtxs["expire"].items():
            self._history_add_rawtx(rawtx, "publish_c2h_expire_tx")
        # ignore commit as they are already added in close method

    def _history_add_rawtx(self, rawtx, action, wallet_tx=True):
        address = None
        if wallet_tx:  # TODO deduce from input/output addresses
            address = keys.address_from_wif(self.api.auth_wif)
        asset_quantity, btc_quantity = self.get_transferred(
            rawtx, asset=self.asset, address=address
        )
        history_add_entry(
            handle=self.handle,
            action=action,
            id=util.gettxid(rawtx),
            fee="{quantity}{asset}".format(
                quantity=abs(btc_quantity), asset="BTC"
            ),
            quantity='{quantity}{asset}'.format(
                quantity=abs(asset_quantity), asset=self.asset
            )
        )

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
        unsigned_c2h_deposit_rawtx = self._make_deposit()
        h2c_deposit_script = self._exchange_deposit_scripts(next_revoke_hash)
        signed_c2h_deposit_rawtx = self.sign(unsigned_c2h_deposit_rawtx,
                                             self.api.auth_wif)
        c2h_deposit_txid = self.publish(signed_c2h_deposit_rawtx)
        self._history_add_published_c2h_deposit(signed_c2h_deposit_rawtx)
        self._set_initial_h2c_state(h2c_deposit_script)
        self._add_to_commits_requested(next_revoke_hash)
        self.payments_sent = []
        self.payments_received = []
        self.payments_queued = []
        self.c2h_commit_delay_time = delay_time
        return c2h_deposit_txid

    def _history_add_micro_send(self, destination, quantity, token):
        history_add_entry(
            handle=self.handle,
            action="queue_micropayment",
            id=token,
            fee="{quantity}{asset}".format(quantity=0, asset=self.asset),
            quantity='{quantity}{asset}'.format(
                quantity=quantity, asset=self.asset
            ),
            destination=destination
        )

    def _history_add_hub_sync(self, id, fee, quantity):
        history_add_entry(
            handle=self.handle,
            action="hub_sync",
            id=id,
            fee="{quantity}{asset}".format(quantity=fee, asset=self.asset),
            quantity='{quantity}{asset}'.format(
                quantity=quantity, asset=self.asset
            )
        )

    def micro_send(self, handle, quantity, token=None):
        """TODO doc string"""

        if token is None:
            token = util.b2h(os.urandom(32))
        self.payments_queued.append({
            "payee_handle": handle,
            "amount": quantity,
            "token": token
        })
        self._history_add_micro_send(handle, quantity, token)
        return token

    def get_status(self, clearance=6):
        netcode = keys.netcode_from_wif(self.api.auth_wif)
        return self.full_duplex_channel_status(
            self.handle, netcode, self.c2h_state,
            self.h2c_state, self.secrets.get, clearance=clearance
        )

    def sync(self):
        """TODO doc string"""

        # always pop payments, they are processed successful or not
        payments = self.payments_queued
        self.payments_queued = []

        # transfer payment funds (create commit/revokes)
        sync_fee = self.channel_terms["sync_fee"]
        quantity = sum([p["amount"] for p in payments]) + sync_fee
        t_result = self.full_duplex_transfer(
            self.api.auth_wif,
            self.secrets.get,
            copy.deepcopy(self.c2h_state),
            copy.deepcopy(self.h2c_state),
            quantity,
            self.c2h_next_revoke_secret_hash,
            self.c2h_commit_delay_time
        )
        commit = t_result["commit"]
        revokes = t_result["revokes"]

        # create next revoke secret for h2c channel
        h2c_next_revoke_secret_hash = self._gen_secret()

        # sync with hub
        s_result = self.api.mph_sync(
            next_revoke_secret_hash=h2c_next_revoke_secret_hash,
            handle=self.handle,
            sends=payments,
            commit=commit,
            revokes=revokes
        )
        self._history_add_hub_sync(
            self.c2h_next_revoke_secret_hash, sync_fee, quantity
        )
        h2c_commit = s_result["commit"]
        c2h_revokes = s_result["revokes"]
        receive_payments = s_result["receive"]
        self.c2h_next_revoke_secret_hash = s_result["next_revoke_secret_hash"]
        self._update_payments(payments, receive_payments)

        # update h2c channel
        self.h2c_state = t_result["recv_state"]
        self._add_to_commits_requested(h2c_next_revoke_secret_hash)
        if h2c_commit:
            self.h2c_state = self.api.mpc_add_commit(
                state=self.h2c_state,
                commit_rawtx=h2c_commit["rawtx"],
                commit_script=h2c_commit["script"]
            )

        # update c2h channel
        self.c2h_state = t_result["send_state"]
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

        # publish h2c commit if possible
        commit_rawtx = self.finalize_commit(self._get_wif, self.h2c_state)
        if commit_rawtx is not None:
            self._history_add_published_h2c_commit(commit_rawtx)

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

        return commit_rawtx

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

        # close channel if needed
        commit_rawtx = None
        h2c_closed = self.api.mpc_published_commits(state=self.h2c_state)
        if self.is_closed(clearance=clearance) and not h2c_closed:
            commit_rawtx = self.close()

        # recover funds if possible
        rawtxs = self.full_duplex_recover_funds(
            self._get_wif, self.secrets.get, self.h2c_state, self.c2h_state
        )

        if commit_rawtx is not None:
            rawtxs["commit"][util.gettxid(commit_rawtx)] = commit_rawtx

        self._history_add_update_rawtxs(rawtxs)
        return rawtxs

    def can_cull(self):
        netcode = keys.netcode_from_wif(self.api.auth_wif)
        scripts = [self.c2h_state["deposit_script"]]
        scripts += [c["script"] for c in self.c2h_state["commits_active"]]
        scripts += [c["script"] for c in self.c2h_state["commits_revoked"]]
        scripts += [c["script"] for c in self.h2c_state["commits_active"]]
        scripts += [c["script"] for c in self.h2c_state["commits_revoked"]]
        for script in scripts:
            address = util.script_address(script, netcode)
            if self.address_in_use(address):
                return False
        return True

    def _get_wif(self, pubkey):
        apk = keys.pubkey_from_wif(self.api.auth_wif)
        assert apk == pubkey, "Auth pubkey {0} != {1}!".format(apk, pubkey)
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
