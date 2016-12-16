import unittest
from tests.mock_rpc_server import start
from picopayments_cli import rpc


class TestRpc(unittest.TestCase):

    def setUp(self):
        self.mock_hub_process = start()

    def tearDown(self):
        self.mock_hub_process.terminate()

    def test_api_auth_call(self):
        auth_wif = "cNXoRUC2eqcBEv1AmvPgM6NgCYV1ReTTHuAmVxaAh6AvVLHroSfU"
        url = "https://127.0.0.1:16000/api/"
        api = rpc.JsonRpc(auth_wif=auth_wif, url=url, verify_ssl_cert=False,
                          username="username", password="password")
        result = api.mph_sync()
        self.assertIn("foo", result)

    def test_api_call_non_existant_method(self):

        def function():
            auth_wif = "cNXoRUC2eqcBEv1AmvPgM6NgCYV1ReTTHuAmVxaAh6AvVLHroSfU"
            url = "https://127.0.0.1:16000/api/"
            api = rpc.JsonRpc(auth_wif=auth_wif, url=url,
                              verify_ssl_cert=False)
            api.non_existant()
        self.assertRaises(rpc.JsonRpcCallFailed, function)


if __name__ == "__main__":
    unittest.main()
