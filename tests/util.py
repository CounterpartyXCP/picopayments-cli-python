import json
import unittest
from picopayments_client import util


FIXTURES = json.load(open("tests/fixtures.json"))


class TestUtils(unittest.TestCase):

    def test_gettxid(self):
        for txid, rawtx in FIXTURES["transactions"].items():
            result = util.gettxid(rawtx)
            self.assertEqual(result, txid)

    def test_wif2address(self):
        for address, wif in FIXTURES["keys"].items():
            result = util.wif2address(wif)
            self.assertEqual(result, address)

    def test_wif2netcode(self):
        for address, wif in FIXTURES["keys"].items():
            result = util.wif2netcode(wif)
            self.assertEqual(result, "XTN")

    def test_pubkey2address(self):
        for address, wif in FIXTURES["keys"].items():
            pubkey = util.wif2pubkey(wif)
            netcode = util.wif2netcode(wif)
            result = util.pubkey2address(pubkey, netcode=netcode)
            self.assertEqual(result, address)

    def test_script2address(self):
        for address, script_hex in FIXTURES["scripts"].items():
            result = util.script2address(script_hex, netcode="XTN")
            self.assertEqual(result, address)

    def test_hash160(self):
        hex_digest = util.hash160hex("f483")
        expected = "4e0123796bee558240c5945ac9aff553fcc6256d"
        self.assertEqual(hex_digest, expected)


if __name__ == "__main__":
    unittest.main()
