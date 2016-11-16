# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


from micropayment_core import util
from micropayment_core import keys
from micropayment_core import scripts


class Mpc(object):

    def __init__(self, api):
        self.api = api  # picopayments_client.rpc.API instance

    def get_rawtx(self, txid):
        """TODO doc string"""
        return self.api.getrawtransaction(tx_hash=txid)

    def get_balances(self, address, assets=None):
        """TODO doc string"""

        # FIXME curruntly includes unconfirmed
        # FIXME add unconfirmed flag
        # https://github.com/CounterpartyXCP/counterblock/blob/master/counterblock/lib/blockchain.py#L108

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
            utxos = self.api.get_unspent_txouts(address=address)
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

        return scripts.sign_deposit(self.get_rawtx, wif, unsigned_rawtx)

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
            self.get_rawtx, wif, unsigned_rawtx, deposit_script_hex
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
                state=recv_state, quantity=revoke_until_quantity,
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
                wif, send_state, send_moved_before + send_quantity,
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
            self.get_rawtx, wif, payout_rawtx, commit_script, spend_secret
        )
        return self.publish(signed_rawtx)

    def recover_revoked(self, get_wif_func, revoke_rawtx, commit_script,
                        revoke_secret):
        pubkey = scripts.get_commit_payer_pubkey(commit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_revoke_recover(
            self.get_rawtx, wif, revoke_rawtx, commit_script, revoke_secret
        )
        return self.publish(signed_rawtx)

    def recover_change(self, get_wif_func, change_rawtx, deposit_script,
                       spend_secret):
        pubkey = scripts.get_deposit_payer_pubkey(deposit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_change_recover(
            self.get_rawtx, wif, change_rawtx, deposit_script, spend_secret
        )
        return self.publish(signed_rawtx)

    def recover_expired(self, get_wif_func, expire_rawtx, deposit_script):
        pubkey = scripts.get_deposit_payer_pubkey(deposit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_expire_recover(
            self.get_rawtx, wif, expire_rawtx, deposit_script
        )
        return self.publish(signed_rawtx)

    def finalize_commit(self, get_wif_func, state):
        commit = self.api.mpc_highest_commit(state=state)
        if commit is None:
            return None
        deposit_script = state["deposit_script"]
        pubkey = scripts.get_deposit_payee_pubkey(deposit_script)
        wif = get_wif_func(pubkey=pubkey)
        signed_rawtx = scripts.sign_finalize_commit(
            self.get_rawtx, wif, commit["rawtx"], deposit_script
        )
        return self.publish(signed_rawtx)

    def full_duplex_recover_funds(self, get_wif_func, get_secret_func,
                                  recv_state, send_state):
        txids = []
        for payout_tx in self.api.mpc_payouts(state=recv_state):
            txids.append(self.recover_payout(
                get_wif_func=get_wif_func,
                get_secret_func=get_secret_func,
                **payout_tx
            ))
        rtxs = self.api.mpc_recoverables(state=send_state)
        for revoke_tx in rtxs["revoke"]:
            txids.append(self.recover_revoke(
                get_wif_func=get_wif_func, **revoke_tx
            ))
        for change_tx in rtxs["change"]:
            txids.append(self.recover_change(
                get_wif_func=get_wif_func, **change_tx
            ))
        for expire_tx in rtxs["expire"]:
            txids.append(self.recover_expired(
                get_wif_func=get_wif_func, **expire_tx
            ))
        return txids
