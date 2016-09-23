import json
import unittest
from picopayments_client import scripts
from picopayments_client import err


FIXTURES = json.load(open("tests/fixtures.json"))


def _get_tx_func(txid):
    return FIXTURES["transactions"][txid]


class TestScripts(unittest.TestCase):

    def test_validate_deposit_script(self):
        scripts.validate_deposit_script(FIXTURES["deposit"]["script_hex"])

    def test_validate_commit_script(self):
        scripts.validate_commit_script(FIXTURES["commit"]["script_hex"])

    def test_validate_incorrect_script(self):

        def function():
            deposit_script_hex = FIXTURES["deposit"]["script_hex"]
            reference_script_hex = scripts.compile_deposit_script(
                "deadbeef", "deadbeef", "deadbeef", "f483"
            )
            scripts.validate(reference_script_hex, deposit_script_hex)
        self.assertRaises(err.InvalidScript, function)

    def test_validate_incorrect_length(self):

        def function():
            deposit_script_hex = FIXTURES["deposit"]["script_hex"] + "f483"
            reference_script_hex = scripts.compile_deposit_script(
                "deadbeef", "deadbeef", "deadbeef", "deadbeef"
            )
            scripts.validate(reference_script_hex, deposit_script_hex)
        self.assertRaises(err.InvalidScript, function)

    def test_get_spend_secret_bad_rawtx(self):
        bad_rawtx = FIXTURES["payout"]["bad_rawtx"]
        commit_script_hex = FIXTURES["payout"]["commit_script_hex"]
        result = scripts.get_spend_secret(bad_rawtx, commit_script_hex)
        self.assertEqual(result, None)

    def test_get_spend_secret(self):
        expected = FIXTURES["payout"]["spend_secret"]
        payout_rawtx = FIXTURES["payout"]["rawtx"]
        commit_script_hex = FIXTURES["payout"]["commit_script_hex"]
        spend_secret = scripts.get_spend_secret(payout_rawtx,
                                                commit_script_hex)
        self.assertEqual(spend_secret, expected)

    def test_get_commit_payer_pubkey(self):
        commit_script_hex = FIXTURES["commit"]["script_hex"]
        expected = FIXTURES["commit"]["payer_pubkey"]
        payer_pubkey = scripts.get_commit_payer_pubkey(commit_script_hex)
        self.assertEqual(payer_pubkey, expected)

    def test_get_commit_payee_pubkey(self):
        commit_script_hex = FIXTURES["commit"]["script_hex"]
        expected = FIXTURES["commit"]["payee_pubkey"]
        payee_pubkey = scripts.get_commit_payee_pubkey(commit_script_hex)
        self.assertEqual(payee_pubkey, expected)

    def test_get_commit_spend_secret_hash(self):
        commit_script_hex = FIXTURES["commit"]["script_hex"]
        expected = FIXTURES["commit"]["spend_secret_hash"]
        spend_secret_hash = scripts.get_commit_spend_secret_hash(
            commit_script_hex
        )
        self.assertEqual(spend_secret_hash, expected)

    def test_get_commit_revoke_secret_hash(self):
        commit_script_hex = FIXTURES["commit"]["script_hex"]
        expected = FIXTURES["commit"]["revoke_secret_hash"]
        revoke_secret_hash = scripts.get_commit_revoke_secret_hash(
            commit_script_hex
        )
        self.assertEqual(revoke_secret_hash, expected)

    def test_get_deposit_expire_time(self):
        deposit_script_hex = FIXTURES["deposit"]["script_hex"]
        expected = FIXTURES["deposit"]["expire_time"]
        expire_time = scripts.get_deposit_expire_time(deposit_script_hex)
        self.assertEqual(expire_time, expected)

    def test_get_deposit_spend_secret_hash(self):
        deposit_script_hex = FIXTURES["deposit"]["script_hex"]
        expected = FIXTURES["deposit"]["spend_secret_hash"]
        spend_secret_hash = scripts.get_deposit_spend_secret_hash(
            deposit_script_hex
        )
        self.assertEqual(spend_secret_hash, expected)

    def test_get_deposit_payer_pubkey(self):
        deposit_script_hex = FIXTURES["deposit"]["script_hex"]
        expected = FIXTURES["deposit"]["payer_pubkey"]
        payer_pubkey = scripts.get_deposit_payer_pubkey(deposit_script_hex)
        self.assertEqual(payer_pubkey, expected)

    def test_get_deposit_payee_pubkey(self):
        deposit_script_hex = FIXTURES["deposit"]["script_hex"]
        expected = FIXTURES["deposit"]["payee_pubkey"]
        payee_pubkey = scripts.get_deposit_payee_pubkey(deposit_script_hex)
        self.assertEqual(payee_pubkey, expected)

    def test_compile_deposit_script(self):
        payer_pubkey = FIXTURES["deposit"]["payer_pubkey"]
        payee_pubkey = FIXTURES["deposit"]["payee_pubkey"]
        spend_secret_hash = FIXTURES["deposit"]["spend_secret_hash"]
        expire_time = FIXTURES["deposit"]["expire_time"]
        expected = FIXTURES["deposit"]["script_hex"]
        deposit_script = scripts.compile_deposit_script(
            payer_pubkey, payee_pubkey, spend_secret_hash, expire_time
        )
        self.assertEqual(deposit_script, expected)

    def test_get_commit_delay_time_gt_max_sequence(self):

        def function():
            script_hex = FIXTURES["commit"]["script_hex_gt_max_sequence"]
            scripts.get_commit_delay_time(script_hex)
        self.assertRaises(err.InvalidSequenceValue, function)

    def test_get_commit_delay_time_lt_min_sequence(self):

        def function():
            script_hex = FIXTURES["commit"]["script_hex_lt_min_sequence"]
            scripts.get_commit_delay_time(script_hex)
        self.assertRaises(err.InvalidSequenceValue, function)

    def test_get_commit_delay_time_zero(self):
        payer_pubkey = FIXTURES["commit"]["payer_pubkey"]
        payee_pubkey = FIXTURES["commit"]["payee_pubkey"]
        spend_secret_hash = FIXTURES["commit"]["spend_secret_hash"]
        revoke_secret_hash = FIXTURES["commit"]["revoke_secret_hash"]
        commit_script_hex = scripts.compile_commit_script(
            payer_pubkey, payee_pubkey, spend_secret_hash,
            revoke_secret_hash, 0
        )
        delay_time = scripts.get_commit_delay_time(commit_script_hex)
        self.assertEqual(delay_time, 0)

    def test_get_commit_delay_time(self):
        commit_script_hex = FIXTURES["commit"]["script_hex"]
        expected = FIXTURES["commit"]["delay_time"]
        delay_time = scripts.get_commit_delay_time(commit_script_hex)
        self.assertEqual(delay_time, expected)

    def test_compile_commit_script(self):
        payer_pubkey = FIXTURES["commit"]["payer_pubkey"]
        payee_pubkey = FIXTURES["commit"]["payee_pubkey"]
        spend_secret_hash = FIXTURES["commit"]["spend_secret_hash"]
        revoke_secret_hash = FIXTURES["commit"]["revoke_secret_hash"]
        delay_time = FIXTURES["commit"]["delay_time"]
        expected = FIXTURES["commit"]["script_hex"]
        commit_script = scripts.compile_commit_script(
            payer_pubkey, payee_pubkey, spend_secret_hash,
            revoke_secret_hash, delay_time
        )
        self.assertEqual(commit_script, expected)

    def test_compile_commit_scriptsig(self):
        pass  # TODO implement

    def test_sign_deposit(self):
        rawtx = scripts.sign_deposit(
            _get_tx_func, **FIXTURES["sign"]["deposit"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["deposit"]["expected"])

    def test_sign_created_commit(self):
        rawtx = scripts.sign_created_commit(
            _get_tx_func, **FIXTURES["sign"]["created_commit"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["created_commit"]["expected"])

    def test_sign_finalize_commit(self):
        rawtx = scripts.sign_finalize_commit(
            _get_tx_func, **FIXTURES["sign"]["finalize_commit"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["finalize_commit"]["expected"])

    def test_sign_finalize_commit_unsigned(self):

        def function():
            kwargs = FIXTURES["sign"]["finalize_commit_unsigned"]["input"]
            scripts.sign_finalize_commit(_get_tx_func, **kwargs)
        self.assertRaises(err.InvalidPayerSignature, function)

    def test_sign_finalize_commit_bad_script(self):

        def function():
            kwargs = FIXTURES["sign"]["finalize_commit_bad_script"]["input"]
            scripts.sign_finalize_commit(_get_tx_func, **kwargs)
        self.assertRaises(ValueError, function)

    def test_sign_revoke_recover(self):
        rawtx = scripts.sign_revoke_recover(
            _get_tx_func, **FIXTURES["sign"]["revoke_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["revoke_recover"]["expected"])

    def test_sign_payout_recover(self):
        rawtx = scripts.sign_payout_recover(
            _get_tx_func, **FIXTURES["sign"]["payout_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["payout_recover"]["expected"])

    def test_sign_change_recover(self):
        rawtx = scripts.sign_change_recover(
            _get_tx_func, **FIXTURES["sign"]["change_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["change_recover"]["expected"])

    def test_sign_expire_recover(self):
        rawtx = scripts.sign_expire_recover(
            _get_tx_func, **FIXTURES["sign"]["expire_recover"]["input"]
        )
        self.assertTrue(rawtx, FIXTURES["sign"]["expire_recover"]["expected"])


if __name__ == "__main__":
    unittest.main()
