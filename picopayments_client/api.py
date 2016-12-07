from jsonrpc import dispatcher
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_client.rpc import JsonRpc
from picopayments_client.mpc import Mpc
from picopayments_client import etc
from micropayment_core import keys


def _hub_api():
    return JsonRpc(
        etc.hub_url, username=etc.hub_username, password=etc.hub_password,
        verify_ssl_cert=etc.hub_verify_ssl_cert
    )


@dispatcher.add_method
def hub_status(asset=None, **kwargs):
    hub_api = _hub_api()
    assets = [asset] if asset else None
    return hub_api.mph_status(assets=assets)


@dispatcher.add_method
def get_balances(asset=None, address=None, **kwargs):
    hub_api = _hub_api()
    assets = [asset] if asset else None
    if address is None:
        address = keys.address_from_wif(get_wif())
    return Mpc(hub_api).get_balances(address, assets=assets)


def get_wif():
    # FIXME load from wallet and generate if doesnt exist
    return "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"


def blockchain_send_funds(asset=None, source=None, address=None,
                          quantity=None, extra_btc=None,
                          **kwargs):
    hub_api = _hub_api()
    assert(asset is not None)
    assert(quantity is not None)
    return Mpc(hub_api).block_send(
        source=get_wif(), destination=address, asset=asset,
        quantity=int(quantity), fee_per_kb=int(etc.fee_per_kb),
        regular_dust_size=int(extra_btc or etc.regular_dust_size),
    )


@Request.application
def _application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def serve_start(**kwargs):
    run_simple(
        kwargs["srv_host"], kwargs["srv_port"],
        _application, processes=1, ssl_context='adhoc'
    )
