import unittest
from micropayment_core import util
from micropayment_core import keys
from picopayments_client import auth


class TestAuth(unittest.TestCase):

    def test_sign_verify_json(self):
        privkey = keys.wif_to_privkey(util.generate_wif())
        signed_json_data = auth.sign_json({"foo": "bar"}, privkey)
        valid = auth.verify_json(signed_json_data)
        self.assertTrue(valid)

    def test_auth_pubkey_missmatch(self):

        def func():
            privkey = keys.wif_to_privkey(util.generate_wif())
            data = {"foo": "bar", "pubkey": "invalid"}
            signed_json_data = auth.sign_json(data, privkey)
            auth.verify_json(signed_json_data)

        self.assertRaises(auth.AuthPubkeyMissmatch, func)


if __name__ == "__main__":
    unittest.main()
