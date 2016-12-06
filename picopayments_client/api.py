from jsonrpc import dispatcher
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_client.rpc import JsonRpc


@dispatcher.add_method
def terms(**kwargs):
    verify = not kwargs["hub_skip_verify"]
    assets = [kwargs["asset"]] if kwargs["asset"] else None
    return JsonRpc(
        kwargs["hub_url"],
        username=kwargs["hub_username"],
        password=kwargs["hub_password"],
        verify_ssl_cert=verify
    ).mph_terms(assets=assets)


@dispatcher.add_method
def hub_funding_addresses(**kwargs):
    verify = not kwargs["hub_skip_verify"]
    return JsonRpc(
        kwargs["hub_url"],
        username=kwargs["hub_username"],
        password=kwargs["hub_password"],
        verify_ssl_cert=verify
    ).mph_funding_addresses()


@Request.application
def _application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def serve_start(**kwargs):
    run_simple(
        kwargs["srv_host"], kwargs["srv_port"],
        _application, processes=1, ssl_context='adhoc'
    )
