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
    """FIXME add doc string"""
    hub_api = _hub_api()
    assets = [asset] if asset else None
    return hub_api.mph_status(assets=assets)


@dispatcher.add_method
def get_balances(asset=None, address=None):
    """FIXME add doc string"""
    hub_api = _hub_api()
    assets = [asset] if asset else None
    if address is None:
        address = keys.address_from_wif(_load_wif())
    return Mpc(hub_api).get_balances(address, assets=assets)


@dispatcher.add_method
def block_send(asset, destination, quantity, extra_btc=0):
    """FIXME add doc string"""
    hub_api = _hub_api()
    kwargs = dict(
        source=_load_wif(),
        destination=destination,
        asset=asset,
        quantity=int(quantity)
    )
    if extra_btc > 0:
        kwargs["regular_dust_size"] = extra_btc
    return Mpc(hub_api).block_send(**kwargs)


@dispatcher.add_method
def connect(asset, quantity, expire_time=1024, delay_time=2):
    """FIXME add doc string"""
    data = _load_data()
    client = Mph(_hub_api())
    send_deposit_txid = client.connect(quantity, expire_time=expire_time,
                                       asset=asset, delay_time=delay_time)
    data["connections"][client.handle] = client.serialize()
    _save_data(data)
    return {
        "send_deposit_txid": send_deposit_txid,
        "handle": client.handle
    }


def _channel_status(hub_api, connection_data, verbose):
    client = Mph.deserialize(hub_api, connection_data)
    status = client.get_status()
    if verbose:
        status["data"] = connection_data
        return status
    else:
        return {
            "asset": status["asset"],
            "balance": status["balance"],
            "ttl": status["ttl"],
            "status": status["status"]
        }



@dispatcher.add_method
def get_status(handle=None, verbose=False):
    """FIXME add doc string"""
    # FIXME have a short and verbose status
    data = _load_data()
    hub_api = _hub_api()
    result = {
        "connections": {},
        "wallet": {
            "address": keys.address_from_wif(_load_wif()),
            "balances": get_balances()
        }
    }
    for _handle, connection_data in data["connections"].items():
        if handle is not None and _handle != handle:
            continue
        result["connections"][_handle] = _channel_status(
            hub_api, connection_data, verbose
        )
    return result


@dispatcher.add_method
def sync(handle=None):
    """FIXME add doc string"""
    result = {}
    data = _load_data()
    hub_api = _hub_api()
    for _handle, connection_data in data["connections"].items():
        if handle is not None and _handle != handle:
            continue
        client = Mph.deserialize(hub_api, connection_data)
        # FIXME auto close channel if needed
        result[_handle] = {
            "txids": client.update(),
            "received_payments": client.sync()
        }
    _save_data(data)
    return result


@dispatcher.add_method
def close(handle):
    """FIXME add doc string"""
    # FIXME test it
    data = _load_data()
    hub_api = _hub_api()
    client = Mph.deserialize(hub_api, data["connections"][handle])
    txids = client.close()
    data["connections"][handle] = client.serialize()
    _save_data(data)
    return txids


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
        data = {"connections": {}}
        _save_data(data)
    return data


def _save_data(data):
    with open(etc.data_path, 'w') as outfile:
        json.dump(data, outfile, indent=2, sort_keys=True)


def serve_api(host=None, port=None):
    run_simple(host, port, _application)
