import os
import json
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_client.rpc import JsonRpc
from picopayments_client.mpc import Mpc
from picopayments_client.mph import Mph
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
    address = keys.address_from_wif(_load_wif())
    return Mpc(hub_api).get_balances(address, assets=assets)


@dispatcher.add_method
def block_send(asset, destination, quantity, extra_btc=0):
    hub_api = _hub_api()
    return Mpc(hub_api).block_send(
        source=_load_wif(), destination=destination, asset=asset,
        quantity=int(quantity), fee_per_kb=int(etc.fee_per_kb),
        regular_dust_size=int(extra_btc or etc.regular_dust_size),
    )


@dispatcher.add_method
def connect(asset, quantity, expire_time=1024, delay_time=2):
    data = _load_data()
    client = Mph(_hub_api())
    send_deposit_txid = client.connect(quantity, expire_time=expire_time,
                                       asset=asset, delay_time=delay_time)
    data["connections"].append(client.serialize())
    _save_data(data)
    return send_deposit_txid


@Request.application
def _application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def _hub_api():
    return JsonRpc(
        etc.hub_url, auth_wif=_load_wif(),
        username=etc.hub_username, password=etc.hub_password,
        verify_ssl_cert=etc.hub_verify_ssl_cert
    )


def _load_wif():
    if not os.path.exists(etc.wallet_path):
        wif = keys.generate_wif(etc.netcode)
        with open(etc.wallet_path, 'w') as outfile:
            outfile.write(wif)
    else:
        with open(etc.wallet_path, 'r', encoding="utf-8") as infile:
            wif = infile.read().strip()
    return wif


def _load_data():
    if os.path.exists(etc.data_path):
        with open(etc.data_path, 'r') as infile:
            data = json.load(infile)
    else:
        data = {"connections": []}
        _save_data(data)
    return data


def _save_data(data):
    with open(etc.data_path, 'w') as outfile:
        json.dump(data, outfile, indent=2, sort_keys=True)


def serve_api(host=None, port=None):
    run_simple(host, port, _application)
