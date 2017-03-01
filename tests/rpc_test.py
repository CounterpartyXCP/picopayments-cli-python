import unittest
import time
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

    def test_parallel_execute(self):

        def func(*args, **kwargs):
            result = sum(args + tuple(kwargs.values()))
            time.sleep(result / 20)
            return result

        results = rpc.parallel_execute([
            dict(name="a", func=func, args=[1, 2, 3], kwargs=dict(a=1, b=4)),
            dict(name="b", func=func, args=[4, 5, 6], kwargs=dict(a=2, b=5)),
            dict(name="c", func=func, args=[7, 8, 9], kwargs=dict(a=3, b=6)),
        ])

        self.assertEqual(results, {'b': 22, 'c': 33, 'a': 11})


if __name__ == "__main__":
    unittest.main()
