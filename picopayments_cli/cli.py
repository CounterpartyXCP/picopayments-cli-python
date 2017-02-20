# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import argparse
from picopayments_cli import parse


def parse_args(args):

    # pre parse testnet to modify defaults depending on network
    testnet = "--testnet" in args

    description = "Decentral micropayment hub for counterparty assets."
    parser = argparse.ArgumentParser(description=description)

    # ===== CONFIG ARGS =====

    # network to use
    parser.add_argument(
        '--testnet', action='store_true', help="Use bitcoin testnet."
    )

    # basedir path
    default = os.path.join(os.path.expanduser("~"), ".picopayments")
    parser.add_argument(
        '--basedir', default=default, metavar="PATH",
        help="Location of app files: {0}".format(default)
    )

    # ===== ADD COMMANDS =====

    subparsers = parser.add_subparsers(
        title='commands', dest='command', metavar="<command>"
    )

    # show version
    subparsers.add_parser("version", help="Show current version number.")

    # get hub status
    command_parser = subparsers.add_parser(
        "hubstatus", help="Get current hub status."
    )
    command_parser.add_argument(
        '--asset', type=parse.asset, default=None, metavar="ASSET",
        help="Optionally limit output to given asset."
    )

    # get balances
    command_parser = subparsers.add_parser(
        "balances", help="Get balances for address or current wallet."
    )
    command_parser.add_argument(
        '--asset', type=parse.asset, default=None, metavar="ASSET",
        help="Optionally filter for given asset."
    )
    command_parser.add_argument(
        '--address', type=parse.address, default=None, metavar="ADDRESS",
        help="Optionally provide address to check, uses wallet by default"
    )

    # search raw transactions
    command_parser = subparsers.add_parser(
        "searchrawtxs", help="Search raw transactions."
    )
    command_parser.add_argument(
        'address', type=parse.address, metavar="ADDRESS",
        help="Address for which to get transactions."
    )
    command_parser.add_argument(
        '--unconfirmed', action='store_true',
        help="Show unconfirmed transactions in result."
    )

    # list utxos for address
    command_parser = subparsers.add_parser(
        "listutxos", help="List utxos for given address."
    )
    command_parser.add_argument(
        'address', type=parse.address, metavar="ADDRESS",
        help="Address for which to get utxos."
    )
    command_parser.add_argument(
        '--unconfirmed', action='store_true',
        help="Show unconfirmed utxos in result."
    )

    # get raw transaction
    command_parser = subparsers.add_parser(
        "getrawtx", help="Gets raw data for a single transaction."
    )
    command_parser.add_argument(
        'txid', type=parse.txid, metavar="STR",
        help="The transaction hash identifier."
    )
    command_parser.add_argument(
        '--verbose', action='store_true',
        help="Include some additional information in the results."
    )

    # blockchain send
    command_parser = subparsers.add_parser(
        "blocksend", help="Send funds via blockchain transaction."
    )
    command_parser.add_argument(
        'asset', type=parse.asset, metavar="ASSET", help="Asset to send"
    )
    command_parser.add_argument(
        'destination', type=parse.address, metavar="ADDRESS",
        help="Address to receive the funds"
    )
    command_parser.add_argument(
        'quantity', type=parse.satoshis, metavar="SATOSHIS",
        help="Quantity of the given asset to transfer."
    )
    command_parser.add_argument(
        '--extra_btc', type=parse.satoshis, default=0, metavar="SATOSHIS",
        help="Optional bitcoin to also be sent."
    )

    # connect to hub
    command_parser = subparsers.add_parser(
        "connect", help="Create micropayment connection with hub."
    )
    command_parser.add_argument(
        'asset', type=parse.asset, metavar="ASSET",
        help="Asset to exchange in connection."
    )
    command_parser.add_argument(
        'quantity', type=parse.satoshis, metavar="SATOSHIS",
        help="Quantity to be bound in the connection deposit."
    )
    command_parser.add_argument(
        '--expire_time', type=parse.sequence, default=1024, metavar="BLOCKS",
        help="Time in blocks after which the deposit expires."
    )
    command_parser.add_argument(
        '--delay_time', type=parse.sequence, default=2, metavar="BLOCKS",
        help="Blocks hub must wait before payout."
    )

    # micro send
    command_parser = subparsers.add_parser(
        "queuepayment", help="Queue micropayment channel send (sent on sync)."
    )
    command_parser.add_argument(
        'source', type=parse.handle, metavar="SOURCE",
        help="Handle of connection to send funds from."
    )
    command_parser.add_argument(
        'destination', type=parse.handle, metavar="DESTINATION",
        help="Handle of connection to receive funds."
    )
    command_parser.add_argument(
        'quantity', type=parse.satoshis, metavar="SATOSHIS",
        help="Quantity of channel asset to transfer."
    )
    command_parser.add_argument(
        '--token', type=parse.token, default=None, metavar="STR",
        help="Optional token payee will receive with the payment."
    )

    # get connections status
    command_parser = subparsers.add_parser(
        "status", help="Get status of connections and wallet."
    )
    command_parser.add_argument(
        '--handle', type=parse.handle, default=None, metavar="HANDLE",
        help="Optionally limit to given handle."
    )
    command_parser.add_argument(
        '--verbose', action='store_true',
        help="Optionally show additional information."
    )

    # sync connections
    command_parser = subparsers.add_parser(
        "sync", help="Sync payments and recover funds from closed connections."
    )
    command_parser.add_argument(
        '--handle', type=parse.handle, default=None, metavar="HANDLE",
        help="Optionally limit to given handle."
    )

    # close connection
    command_parser = subparsers.add_parser(
        "close", help="Close open connection and settle to blockchain."
    )
    command_parser.add_argument(
        'handle', type=parse.handle, metavar="HANDLE",
        help="Handle of connection to close."
    )

    # show history
    command_parser = subparsers.add_parser(
        "history", help="Show history"
    )
    command_parser.add_argument(
        '--handle', type=parse.handle, default=None, metavar="HANDLE",
        help="Limit history to given channel."
    )

    # cull closed connections no longer needed
    command_parser = subparsers.add_parser(
        "cull",
        help="Removes closed channels if all funds have been recovered."
    )
    command_parser.add_argument(
        '--handle', type=parse.handle, default=None, metavar="HANDLE",
        help="Optional handle of specific connection to be cull."
    )

    # cancel queued payment
    command_parser = subparsers.add_parser(
        "cancelpayment", help="Cancel queued but unsynced payment."
    )
    command_parser.add_argument(
        'token', type=parse.token, metavar="TOKEN",
        help="Token of the queued payment to be canceled."
    )

    # start rpc api server
    command_parser = subparsers.add_parser(
        "serve", help="Start RPC-API server."
    )
    command_parser.add_argument(
        '--host', type=parse.host, default="localhost", metavar="HOST",
        help="RPC-API server host: {0}".format("localhost")
    )
    default = 16000 if testnet else 6000
    command_parser.add_argument(
        '--port', type=parse.port, default=default, metavar="PORT",
        help="RPC-API server port: {0}".format(default)
    )

    return vars(parser.parse_args(args=args)), parser
