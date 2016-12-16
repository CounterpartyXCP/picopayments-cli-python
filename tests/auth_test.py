import unittest
from micropayment_core import keys
from picopayments_cli import auth


class TestAuth(unittest.TestCase):

    def test_sign_verify_json(self):
        auth_wif = keys.generate_wif()
        signed_json_data = auth.sign_json({"foo": "bar"}, auth_wif)
        valid = auth.verify_json(signed_json_data)
        self.assertTrue(valid)

    def test_auth_pubkey_missmatch(self):

        def func():
            auth_wif = keys.generate_wif()
            data = {"foo": "bar", "pubkey": "invalid"}
            signed_json_data = auth.sign_json(data, auth_wif)
            auth.verify_json(signed_json_data)

        self.assertRaises(auth.AuthPubkeyMissmatch, func)


if __name__ == "__main__":
    unittest.main()
