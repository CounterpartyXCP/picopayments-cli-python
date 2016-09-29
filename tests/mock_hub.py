import time
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from multiprocessing import Process
from picopayments_client import auth


@dispatcher.add_method
def test_auth(**kwargs):
    auth.verify_json(kwargs)
    authwif = "cT9pEqELRn5v67hJmmmYQmPnsuezJeup7CqQiJBUTZnLLoxdydAb"
    return auth.sign_json({"foo": "bar"}, authwif)


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def start():
    process = Process(
        target=run_simple,
        args=('127.0.0.1', 16000, application),
        kwargs=dict(processes=1, ssl_context='adhoc')
    )
    process.start()
    time.sleep(5)
    return process


if __name__ == "__main__":
    run_simple(
        *('127.0.0.1', 16000, application),
        **dict(processes=1, ssl_context='adhoc')
    )
