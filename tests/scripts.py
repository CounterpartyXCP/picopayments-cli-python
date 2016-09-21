import json
import unittest
from picopayments_client import scripts


FIXTURES = json.load(open("tests/fixtures.json"))


def _get_tx_func(txid):
    return FIXTURES["transactions"][txid]


class TestScripts(unittest.TestCase):

    def test_sign_deposit(self):
        rawtx = scripts.sign_deposit(
            _get_tx_func, **FIXTURES["deposit"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["deposit"]["expected"])

    def test_sign_created_commit(self):
        rawtx = scripts.sign_created_commit(
            _get_tx_func, **FIXTURES["created_commit"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["created_commit"]["expected"])

    def test_sign_finalize_commit(self):
        rawtx = scripts.sign_finalize_commit(
            _get_tx_func, **FIXTURES["finalize_commit"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["finalize_commit"]["expected"])

    def test_sign_revoke_recover(self):
        rawtx = scripts.sign_revoke_recover(
            _get_tx_func, **FIXTURES["revoke_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["revoke_recover"]["expected"])

    def test_sign_payout_recover(self):
        rawtx = scripts.sign_payout_recover(
            _get_tx_func, **FIXTURES["payout_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["payout_recover"]["expected"])

    def test_sign_change_recover(self):
        rawtx = scripts.sign_change_recover(
            _get_tx_func, **FIXTURES["change_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["change_recover"]["expected"])

    def test_sign_expire_recover(self):
        rawtx = scripts.sign_expire_recover(
            _get_tx_func, **FIXTURES["expire_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["expire_recover"]["expected"])


if __name__ == "__main__":
    unittest.main()
