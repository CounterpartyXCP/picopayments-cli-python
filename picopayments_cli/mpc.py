# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import csv
import time
from micropayment_core import util
from micropayment_core import keys
from micropayment_core import scripts
from picopayments_cli import etc


HISTORY_FIELDNAMES = [
    'timestamp',
    'handle',
    'action',
    'id',  # txid, token, revoke secret?
    'fee',
    'quantity',
    'destination'
]


def history_add_entry(**kwargs):
    if etc.history_path is not None:

        # add missing fields
        kwargs["timestamp"] = "{0}".format(time.time())
        for fieldname in HISTORY_FIELDNAMES:
            if fieldname not in kwargs:
                kwargs[fieldname] = ""

        # update history file
        writeheader = not os.path.exists(etc.history_path)
        with open(etc.history_path, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HISTORY_FIELDNAMES)
            if writeheader:
                writer.writeheader()
            writer.writerow(kwargs)


class Mpc(object):

    def __init__(self, api):
        self.api = api  # picopayments_cli.rpc.API instance

    def _btc_transferred(self, rawtx, address):

        netcode = keys.netcode_from_address(address)
        tx = util.load_tx(self.get_rawtxs, rawtx)

        total = 0
        for tx_out in tx.txs_out:
            try:
                if tx_out.bitcoin_address(netcode=netcode) == address:
                    total += tx_out.coin_value
            except Exception:
                pass  # XXX work around pycoin bug
        if not tx.is_coinbase():
            for tx_out in tx.unspents:
                if tx_out.bitcoin_address(netcode=netcode) == address:
                    total -= tx_out.coin_value
        return total

    def get_transferred(self, rawtx, asset=None, address=None):
        quantity = 0
        try:
            src, dest, btc, fee, data = self.api.get_tx_info(tx_hex=rawtx)
            if data:
                message_type_id, unpacked = self.api.unpack(data_hex=data)
                if message_type_id == 0:
                    assert(asset is None or asset == unpacked["asset"])
                    assert(address is None or address ==
                           src or address == dest)

                    # by default return payee view
                    if address is None or dest == address:
                        return unpacked["quantity"], btc

                    quantity = -unpacked["quantity"]
        except Exception:  # TODO catch specific expected exceptions
            pass  # not a counterparty tx

        # must count tx outputs - inputs for payer view
        return quantity, self._btc_transferred(rawtx, address)

    def get_rawtxs(self, txids):
        """TODO doc string"""
        return self.api.getrawtransaction_batch(txhash_list=txids)

    def address_in_use(self, address):
        for asset, quantity in self.get_balances(address).items():
            if quantity != 0:
                return True
        if self.api.get_unspent_txouts(address=address, unconfirmed=True):
            return True
        return False

    def get_balances(self, address, assets=None):
        """Get confirmed balances for given assets."""

        # get asset balances
        entries = self.api.get_balances(filters=[
            {"field": "address", "op": "==", "value": address},
        ])
        result = {}
        for entrie in entries:
            if assets and entrie["asset"] not in assets:
                continue
            result[entrie["asset"]] = entrie["quantity"]

        # fill in zero balance assets
        if assets is not None:
            for asset in assets:
                result[asset] = result.get(asset, 0)

        # get btc balance
        if assets is None or "BTC" in assets:
            utxos = self.api.get_unspent_txouts(
                address=address, unconfirmed=False
            )
            balance = sum(map(lambda u: util.to_satoshis(u["amount"]), utxos))
            result["BTC"] = balance

        return result

    def block_send(self, **kwargs):
        """TODO doc string"""

        # replace source wif with address
        wif = kwargs.pop("source")
        kwargs["source"] = keys.address_from_wif(wif)

        # create, sign and publish transaction
        unsigned_rawtx = self.api.create_send(**kwargs)
        signed_rawtx = self.sign(unsigned_rawtx, wif)
        return self.publish(signed_rawtx)

    def sign(self, unsigned_rawtx, wif):
        """TODO doc string"""

        return scripts.sign_deposit(self.get_rawtxs, wif, unsigned_rawtx)

    def publish(self, rawtx):
        return self.api.sendrawtransaction(tx_hex=rawtx)

    def create_signed_commit(self, wif, state, quantity,
                             revoke_secret_hash, delay_time):

        # create commit
        result = self.api.mpc_create_commit(
            state=state, revoke_secret_hash=revoke_secret_hash,
            delay_time=delay_time, quantity=quantity
        )
        state = result["state"]
        commit_script = result["commit_script"]
        unsigned_rawtx = result["tosign"]["commit_rawtx"]
        deposit_script_hex = result["tosign"]["deposit_script"]

        # sign commit
        signed_rawtx = scripts.sign_created_commit(
            self.get_rawtxs, wif, unsigned_rawtx, deposit_script_hex
        )

        # replace unsigned rawtx of state commit with signed rawtx
        for commit in state["commits_active"]:
            if commit["script"] == commit_script:
                commit["rawtx"] = signed_rawtx

        return {
            "state": state,
            "commit": {"rawtx": signed_rawtx, "script": commit_script}
        }

    def full_duplex_transfer(self, wif, get_secret_func, send_state,
                             recv_state, quantity,
                             send_next_revoke_secret_hash,
                             send_commit_delay_time):
        commit = None
        revokes = []

        # revoke what we can to maximize liquidity
        recv_moved_before = self.api.mpc_transferred_amount(state=recv_state)
        if recv_moved_before > 0:
            revoke_until_quantity = max(recv_moved_before - quantity, 0)

            # get hashes of secrets to publish
            revoke_hashes = self.api.mpc_revoke_hashes_until(
                state=recv_state,
                quantity=revoke_until_quantity,
                surpass=False  # never revoke past the given quantity!!!
            )

            # get secrets to publish
            revokes += [get_secret_func(h) for h in revoke_hashes]

            # revoke commits for secrets that will be published
            if revokes:
                recv_state = self.api.mpc_revoke_all(
                    state=recv_state, secrets=revokes
                )

        # create commit to send the rest
        recv_moved_after = self.api.mpc_transferred_amount(state=recv_state)
        recv_revoked_quantity = recv_moved_before - recv_moved_after
        send_quantity = quantity - recv_revoked_quantity
        send_moved_before = self.api.mpc_transferred_amount(state=send_state)
        if send_quantity > 0:
            result = self.create_signed_commit(
                wif,
                send_state,
                send_moved_before + send_quantity,
                send_next_revoke_secret_hash,
                send_commit_delay_time
            )
            send_state = result["state"]
            commit = result["commit"]

        return {
            "send_state": send_state, "recv_state": recv_state,
            "revokes": revokes, "commit": commit
        }

    def recover_payout(self, get_wif_func, get_secret_func, payout_rawtx,
                       commit_script):
        pubkey = scripts.get_commit_payee_pubkey(commit_script)
        wif = get_wif_func(pubkey=pubkey)
        spend_secret_hash = scripts.get_commit_spend_secret_hash(commit_script)
        spend_secret = get_secret_func(spend_secret_hash)
        signed_rawtx = scripts.sign_payout_recover(
            self.get_rawtxs, wif, payout_rawtx, commit_script, spend_secret
        )
        if self.publish(signed_rawtx):
            return signed_rawtx
        return None

    def recover_revoked(self, get_wif_func, revoke_rawtx, commit_script,
                        revoke_secret):
        pubkey = scripts.get_commit_payer_pubkey(commit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_revoke_recover(
            self.get_rawtxs, wif, revoke_rawtx, commit_script, revoke_secret
        )
        if self.publish(signed_rawtx):
            return signed_rawtx
        return None

    def recover_change(self, get_wif_func, change_rawtx, deposit_script,
                       spend_secret):
        pubkey = scripts.get_deposit_payer_pubkey(deposit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_change_recover(
            self.get_rawtxs, wif, change_rawtx, deposit_script, spend_secret
        )
        if self.publish(signed_rawtx):
            return signed_rawtx
        return None

    def recover_expired(self, get_wif_func, expire_rawtx, deposit_script):
        pubkey = scripts.get_deposit_payer_pubkey(deposit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_expire_recover(
            self.get_rawtxs, wif, expire_rawtx, deposit_script
        )
        if self.publish(signed_rawtx):
            return signed_rawtx
        return None

    def _can_publish(self, rawtx, deposit_utxos):

        # check utxos not spent
        tx = util.load_tx(self.get_rawtxs, rawtx)
        for tx_in in tx.txs_in:
            if tx_in.is_coinbase():
                continue

            found = False
            for utxo in deposit_utxos:
                txid = util.b2h_rev(tx_in.previous_hash)
                vout = tx_in.previous_index
                if (utxo["txid"] == txid and utxo["vout"] == vout):
                    found = True
                    break
            if not found:
                return False

        return tx.bad_signature_count() == 0

    def finalize_commit(self, get_wif_func, state):
        commit = self.api.mpc_highest_commit(state=state)
        if commit is None:
            return None
        deposit_script = state["deposit_script"]
        pubkey = scripts.get_deposit_payee_pubkey(deposit_script)
        wif = get_wif_func(pubkey=pubkey)
        rawtx = scripts.sign_finalize_commit(
            self.get_rawtxs, wif, commit["rawtx"], deposit_script
        )

        netcode = keys.netcode_from_wif(wif)
        deposit_address = util.script_address(deposit_script, netcode)
        deposit_utxos = self.api.get_unspent_txouts(address=deposit_address,
                                                    unconfirmed=False)

        if self._can_publish(rawtx, deposit_utxos) and self.publish(rawtx):
            return rawtx
        return None

    def full_duplex_recover_funds(self, get_wif_func, get_secret_func,
                                  recv_state, send_state):

        # get send spend secret if known
        send_spend_secret_hash = scripts.get_deposit_spend_secret_hash(
            send_state["deposit_script"]
        )
        send_spend_secret = get_secret_func(send_spend_secret_hash)

        rawtxs = {
            "payout": {},  # {"txid": "rawtx"}
            "revoke": {},  # {"txid": "rawtx"}
            "change": {},  # {"txid": "rawtx"}
            "expire": {},  # {"txid": "rawtx"}
            "commit": {}   # {"txid": "rawtx"}
        }

        # get payouts
        for payout_tx in self.api.mpc_payouts(state=recv_state):
            rawtx = self.recover_payout(
                get_wif_func=get_wif_func,
                get_secret_func=get_secret_func,
                **payout_tx
            )
            rawtxs["payout"][util.gettxid(rawtx)] = rawtx

        rtxs = self.api.mpc_recoverables(state=send_state,
                                         spend_secret=send_spend_secret)
        for revoke_tx in rtxs["revoke"]:
            rawtx = self.recover_revoked(
                get_wif_func=get_wif_func, **revoke_tx
            )
            rawtxs["revoke"][util.gettxid(rawtx)] = rawtx

        for change_tx in rtxs["change"]:
            rawtx = self.recover_change(
                get_wif_func=get_wif_func, **change_tx
            )
            rawtxs["change"][util.gettxid(rawtx)] = rawtx

        for expire_tx in rtxs["expire"]:
            rawtx = self.recover_expired(
                get_wif_func=get_wif_func, **expire_tx
            )
            rawtxs["expire"][util.gettxid(rawtx)] = rawtx

        return rawtxs

    def full_duplex_channel_status(self, handle, netcode, send_state,
                                   recv_state, get_secret_func, clearance=6):
        assert(send_state["asset"] == recv_state["asset"])
        asset = send_state["asset"]

        send_ttl = self.api.mpc_deposit_ttl(state=send_state,
                                            clearance=clearance)
        send_script = send_state["deposit_script"]
        send_deposit_expire_time = scripts.get_deposit_expire_time(send_script)
        send_deposit_address = util.script_address(
            send_script, netcode=netcode
        )
        send_balances = self.get_balances(send_deposit_address, ["BTC", asset])
        send_deposit = send_balances.get(asset, 0)
        send_transferred = 0
        if len(send_state["commits_active"]) > 0:
            send_transferred = self.api.mpc_transferred_amount(
                state=send_state
            )

        recv_ttl = self.api.mpc_deposit_ttl(state=recv_state,
                                            clearance=clearance)
        recv_script = recv_state["deposit_script"]
        recv_deposit_expire_time = scripts.get_deposit_expire_time(recv_script)
        recv_deposit_address = util.script_address(
            recv_script, netcode=netcode
        )
        recv_balances = self.get_balances(recv_deposit_address, ["BTC", asset])
        recv_deposit = recv_balances.get(asset, 0)
        recv_transferred = 0
        if len(recv_state["commits_active"]) > 0:
            recv_transferred = self.api.mpc_transferred_amount(
                state=recv_state
            )

        send_balance = send_deposit + recv_transferred - send_transferred
        recv_balance = recv_deposit + send_transferred - recv_transferred

        ttl = None
        if send_ttl is not None and recv_ttl is not None:
            ttl = min(send_ttl, recv_ttl)

        # get connection status
        status = "opening"
        if send_ttl and recv_ttl:
            status = "open"
        send_secret_hash = scripts.get_deposit_spend_secret_hash(send_script)
        send_secret = get_secret_func(send_secret_hash)
        send_commits_published = self.api.mpc_published_commits(
            state=send_state
        )
        expired = ttl == 0  # None explicitly ignore as channel opening
        if expired or send_secret or send_commits_published:
            status = "closed"
            send_balance = send_deposit
            recv_balance = 0

        return {
            # TODO get channel tx history
            "status": status,
            "asset": asset,
            "netcode": netcode,
            "balance": send_balance,
            "ttl": ttl,
            "send_balance": send_balance,
            "send_deposit_address": send_deposit_address,
            "send_deposit_ttl": send_ttl,
            "send_deposit_balances": send_balances,
            "send_deposit_expire_time": send_deposit_expire_time,
            "send_commits_published": send_commits_published,
            "send_transferred_quantity": send_transferred,
            "recv_balance": recv_balance,
            "recv_deposit_address": recv_deposit_address,
            "recv_deposit_ttl": recv_ttl,
            "recv_deposit_balances": recv_balances,
            "recv_deposit_expire_time": recv_deposit_expire_time,
            "recv_transferred_quantity": recv_transferred,
        }
