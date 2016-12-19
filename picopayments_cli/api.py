import os
import copy
import json
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_cli.rpc import JsonRpc
from picopayments_cli.mpc import Mpc
from picopayments_cli.mph import Mph
from picopayments_cli import etc
from picopayments_cli import __version__
from micropayment_core import keys


@dispatcher.add_method
def version():
    """ Returns current version of number. """
    return __version__


@dispatcher.add_method
def hubstatus(asset=None):
    """ Get current hub status.

    Args:
        asset (str): Optionally limit output to given asset.

    Returns:
        List of open connections, current terms, funding addresses
        and current liquidity for new connections.

        {
          "connections": {
            "a0b1156206dedb1aa24084752b5693a9022349dc547fb9952aa510003e93": {
              "asset": "XCP",
              "balance": 31338,
              "status": "open",
              "ttl": 401
            }
          },
          "current_terms": {
            "XCP": {
              "deposit_max": 0,
              "deposit_min": 0,
              "deposit_ratio": 1.0,
              "expire_max": 0,
              "expire_min": 0,
              "sync_fee": 1
            }
          },
          "funding_addresses": {
            "BTC": "mhzPMMC3hkQUL9HUYY13s2NehEJXCA923Z",
            "XCP": "n1f73Cvxi7KFWK5p7W8F6JYbyQxV5djqUo"
          },
          "liquidity": {
            "addresses": {
              "XCP": [
                {
                  "address": "mzEPqJet1LvZK5wjeDqmYx4udC3zx9oFwm",
                  "balances": {
                    "BTC": 333600,
                    "XCP": 399876544
                  }
                }
              ]
            },
            "total": {
              "BTC": 807814,
              "XCP": 599845207
            }
          }
        }
    """
    hub_api = _hub_api()
    assets = [asset] if asset else None
    return hub_api.mph_status(assets=assets)


@dispatcher.add_method
def balances(asset=None, address=None):
    """ Get balances for address or current wallet.

    Args:
        asset (str, default=None): Optionally filter for given asset.
        address (str, default=None): Optionally provide address to check,
                                     uses wallet by default

    Returns:
        Dict mapping asset to available quantity in satoshis,
        Unconfirmed assets are ignored.

        {
            "BTC": 926109330,
            "XCP": 140982404156
        }
    """
    hub_api = _hub_api()
    assets = [asset] if asset else None
    if address is None:
        address = keys.address_from_wif(_load_wif())
    return Mpc(hub_api).get_balances(address, assets=assets)


@dispatcher.add_method
def blocksend(asset, destination, quantity, extra_btc=0):
    """ Send funds using via blockchain transaction.

    Args:
        asset (str): Asset to send.
        destination (address): Address to receive the funds.
        quantity (int): Quantity of the given asset to transfer.
        extra_btc (int, default=0): Optional bitcoin to also be sent.

    Returns:
        txid of published transaction.
    """
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
    """ Create micropayment connection with hub.

    Args:
        asset (str): Asset to exchange in connection.
        quantity (str): Quantity to be bound in the deposit, this determins
                        the maximum amount that can bet transferred.
        expire_time (int, default=1024): Time in blocks after which the
                                         deposit expires and can be recovered.
        delay_time (int, default=2): Blocks hub must wait before payout,
                                     protects against publish revoked commits.

    Returns:
        {
            "send_deposit_txid": "published bitcoin transaction id",
            "handle": "handle for created connection"
        }
    """

    # connect to hub
    client = Mph(_hub_api())
    send_deposit_txid = client.connect(quantity, expire_time=expire_time,
                                       asset=asset, delay_time=delay_time)

    # save to data
    data = _load_data()
    data["connections"][client.handle] = client.serialize()
    _save_data(data)

    return {
        "send_deposit_txid": send_deposit_txid,
        "handle": client.handle
    }


@dispatcher.add_method
def queuepayment(source, destination, quantity, token=None):
    """ Queue micropayment channel send (sent on sync).

    Args:
        source (str): Handle of connection to send funds from.
        destination (str): Handle of connection to receive funds.
        quantity (int): Quantity of channel asset to transfer.
        token (str, default=None): Optional token payee will
                                   receive with the payment.

    Returns:
        Provided token or generated token if None given.
    """
    hub_api = _hub_api()
    data = _load_data()
    client = Mph.deserialize(hub_api, data["connections"][source])
    # FIXME check dest can receive payment
    result = client.micro_send(destination, quantity, token=token)
    data["connections"][source] = client.serialize()
    _save_data(data)
    return result


@dispatcher.add_method
def status(handle=None, verbose=False):
    """ Get status of connections and wallet.

    Args:
        handle (str, default=None): Optionally limit to given handle.
        verbose (bool, default=False): Optionally show additional information.

    Returns:
        {
          "connections": {
            "a0b206d1f68edb1aa24084752b5693a9022349dc547fb9952aa510003e93": {
              "asset": "XCP",
              "balance": 31337,
              "status": "open",
              "ttl": 404
            }
          },
          "wallet": {
            "address": "n2WQGAvnDS1vf7uXToLou6kLxJXRGFHo2b",
            "balances": {
              "BTC": 926109330,
              "XCP": 140982404156
            }
          }
        }
    """
    data = _load_data()
    hub_api = _hub_api()
    result = {
        "connections": {},
        "wallet": {
            "address": keys.address_from_wif(_load_wif()),
            "balances": balances()
        }
    }
    for _handle, connection_data in data["connections"].items():
        if handle is not None and _handle != handle:
            continue
        client = Mph.deserialize(hub_api, connection_data)
        status = client.get_status()
        if verbose:
            status["data"] = connection_data
            result["connections"][_handle] = status
        else:
            result["connections"][_handle] = {
                "asset": status["asset"],
                "balance": status["balance"],
                "ttl": status["ttl"],
                "status": status["status"]
            }
    return result


@dispatcher.add_method
def sync(handle=None):
    """ Sync payments and recover funds from closed connections.

    This WILL cost a fee per channnel synced as defined in the hub terms.

    * Synchronize open connections to send/receive payments.
    * Recover funds of closed connections.

    Args:
        handle (str, default=None): Optionally limit to given handle.

    Returns:
        {
          "connection handle": {
            "txids": ["of transactions publish while recovering funds"],
            "received_payments": [
              {
                "payer_handle": "sender handle",
                "amount": 1337,
                "token": "provided by sender"
              }
            ]
          }
        }
    """
    result = {}
    hub_api = _hub_api()
    data = _load_data()
    for _handle, connection_data in copy.deepcopy(data)["connections"].items():
        if handle is not None and _handle != handle:
            continue
        client = Mph.deserialize(hub_api, connection_data)
        status = client.get_status()

        # sync open connections
        if status["status"] == "open":
            result[_handle] = {
                "txids": [],
                "received_payments": client.sync()
            }

        # update closed connections
        elif status["status"] == "closed":
            result[_handle] = {
                "txids": client.update(),
                "received_payments": []
            }

            # FIXME remove connection if all funds recovered

        data["connections"][client.handle] = client.serialize()

    _save_data(data)
    return result


@dispatcher.add_method
def close(handle):
    """ Close open connection and settle to blockchain.

    Args:
        handle (str): Handle of connection to close.

    Returns:
        Commit txid or None if no assets received from hub.
    """
    hub_api = _hub_api()
    data = _load_data()
    client = Mph.deserialize(hub_api, data["connections"][handle])
    commit_txid = client.close()
    # FIXME recover now if possible
    data["connections"][handle] = client.serialize()
    _save_data(data)
    return commit_txid


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


def serve(host, port):
    """ Start RPC-API Server.

    Args:
        host (str): Network interface on which to host the service.
        port (int): Network port on which to host the service.
    """
    run_simple(host, port, _application)
