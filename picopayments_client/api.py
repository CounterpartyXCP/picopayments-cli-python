from jsonrpc import dispatcher
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_client.rpc import JsonRpc
from picopayments_client.mpc import Mpc


def _hub_api(**kwargs):
    verify = not kwargs["hub_skip_verify"]
    return JsonRpc(
        kwargs["hub_url"], username=kwargs["hub_username"],
        password=kwargs["hub_password"], verify_ssl_cert=verify
    )


@dispatcher.add_method
def terms(asset=None, **kwargs):
    hub_api = _hub_api(**kwargs)
    assets = [asset] if asset else None
    return hub_api.mph_terms(assets=assets)


@dispatcher.add_method
def hub_funding_addresses(**kwargs):
    hub_api = _hub_api(**kwargs)
    return hub_api.mph_funding_addresses()


@dispatcher.add_method
def get_balances(asset=None, address=None, **kwargs):
    hub_api = _hub_api(**kwargs)
    assets = [asset] if asset else None
    # FIXME get wallet address if none given
    return Mpc(hub_api).get_balances(address, assets=assets)


def blockchain_send_funds(asset=None, source=None, address=None,
                          quantity=None, extra_btc=None,
                          regular_dust_size=None, fee_per_kb=None,
                          **kwargs):
    hub_api = _hub_api(**kwargs)
    assert(asset is not None)
    assert(source is not None)  # FIXME get wallet wif if none given
    assert(quantity is not None)
    return Mpc(hub_api).block_send(
        source=source, destination=address, asset=asset,
        quantity=int(quantity),
        fee_per_kb=int(fee_per_kb),
        regular_dust_size=int(extra_btc or regular_dust_size),
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
