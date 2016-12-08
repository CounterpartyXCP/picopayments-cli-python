import os
from jsonrpc import dispatcher
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_client.rpc import JsonRpc
from picopayments_client.mpc import Mpc
from picopayments_client import etc
from picopayments_client import __version__
from micropayment_core import keys


@dispatcher.add_method
def version():
    return __version__


@dispatcher.add_method
def get_hub_status(asset=None):
    hub_api = _hub_api()
    assets = [asset] if asset else None
    return hub_api.mph_status(assets=assets)


@dispatcher.add_method
def get_balances(asset=None):
    hub_api = _hub_api()
    assets = [asset] if asset else None
    address = keys.address_from_wif(_get_wif())
    return Mpc(hub_api).get_balances(address, assets=assets)


@dispatcher.add_method
def block_send(asset, destination, quantity, extra_btc=0):
    hub_api = _hub_api()
    return Mpc(hub_api).block_send(
        source=_get_wif(), destination=destination, asset=asset,
        quantity=int(quantity), fee_per_kb=int(etc.fee_per_kb),
        regular_dust_size=int(extra_btc or etc.regular_dust_size),
    )


@dispatcher.add_method
def connect(asset, quantity, expire_time=1024, delay_time=2):
    pass


@Request.application
def _application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def _hub_api():
    privkey = keys.wif_to_privkey(_get_wif())
    return JsonRpc(
        etc.hub_url, privkey=privkey,
        username=etc.hub_username, password=etc.hub_password,
        verify_ssl_cert=etc.hub_verify_ssl_cert
    )


def _get_wif():
    if not os.path.exists(etc.wallet_path):
        wif = keys.generate_wif(etc.netcode)
        with open(etc.wallet_path, 'w') as outfile:
            outfile.write(wif)
    else:
        with open(etc.wallet_path, 'r', encoding="utf-8") as infile:
            wif = infile.read().strip()
    return wif


def serve_api(host=None, port=None):
    run_simple(host, port, _application)
