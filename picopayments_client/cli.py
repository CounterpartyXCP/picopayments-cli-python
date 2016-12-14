# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import argparse


def parse(args):

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
        "hub_status", help="Get current hub status."
    )
    command_parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="Optionally filter for given asset."
    )

    # get balances
    command_parser = subparsers.add_parser(
        "balances", help="Get balances for wallet."
    )
    command_parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="Optionally filter for given asset."
    )
    command_parser.add_argument(
        '--address', default=None, metavar="ADDRESS",
        help="Optionally provide address to check (wallet by default)"
    )

    # blockchain send
    command_parser = subparsers.add_parser(
        "block_send", help="Send funds via blockchain transaction."
    )
    command_parser.add_argument(
        'asset', metavar="ASSET",
        help="Optionally filter for given asset."
    )
    command_parser.add_argument(
        'destination', metavar="ADDRESS",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        'quantity', type=int, metavar="QUANTITY",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        '--extra_btc', type=int, default=0, metavar="SATOSHIS",
        help="FIXME doc string"
    )

    # micro send
    command_parser = subparsers.add_parser(
        "micro_send", help="Send funds via micropayment channel."
    )
    command_parser.add_argument(
        'source', metavar="SOURCE",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        'destination', metavar="DESTINATION",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        'quantity', type=int, metavar="QUANTITY",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        '--token', default=None, metavar="STR",
        help="FIXME doc string"
    )

    # start rpc api server
    command_parser = subparsers.add_parser(
        "serve", help="Start RPC-API server."
    )
    command_parser.add_argument(
        '--host', default="localhost", metavar="PORT",
        help="RPC-API server host: {0}".format("localhost")
    )
    default = 16000 if testnet else 6000
    command_parser.add_argument(
        '--port', type=int, default=default, metavar="PORT",
        help="RPC-API server port: {0}".format(default)
    )

    # connect to hub
    command_parser = subparsers.add_parser(
        "connect", help="Create micropayment connection with hub."
    )
    command_parser.add_argument(
        'asset', metavar="ASSET",
        help="Optionally filter for given asset."
    )
    command_parser.add_argument(
        'quantity', type=int, metavar="QUANTITY",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        '--expire_time', type=int, default=1024, metavar="BLOCKS",
        help="FIXME doc string"
    )
    command_parser.add_argument(
        '--delay_time', type=int, default=2, metavar="BLOCKS",
        help="FIXME doc string"
    )

    # get connections status
    command_parser = subparsers.add_parser(
        "status", help="Get status of connections."
    )
    command_parser.add_argument(
        '--handle', default=None, metavar="HANDLE",
        help="Only show status for given handle."
    )
    command_parser.add_argument(
        '--verbose', action='store_true',
        help="Verbose connection status output."
    )

    # sync connections
    command_parser = subparsers.add_parser(
        "sync", help="Sync open connections and recover closed funds."
    )
    command_parser.add_argument(
        '--handle', default=None, metavar="HANDLE",
        help="Handle of channel to sync."
    )

    # close connection
    command_parser = subparsers.add_parser(
        "close", help="Close connection."
    )
    command_parser.add_argument(
        'handle', metavar="HANDLE",
        help="Handle of channel to close."
    )

    return vars(parser.parse_args(args=args)), parser
