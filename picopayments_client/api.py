from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher


@Request.application
def _application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def serve(**kwargs):
    run_simple(
        kwargs["host"], kwargs["port"], _application,
        processes=1, ssl_context='adhoc'
    )
