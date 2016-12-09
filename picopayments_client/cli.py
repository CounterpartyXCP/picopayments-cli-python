# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import sys
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
        "get_hub_status", help="Get current hub status."
    )
    command_parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="Optionally filter for given asset."
    )

    # get balances
    command_parser = subparsers.add_parser(
        "get_balances", help="Get balances for wallet."
    )
    command_parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="Optionally filter for given asset."
    )

    # blockchain send
    command_parser = subparsers.add_parser(
        "block_send", help="Send funds using a blockchain transaction."
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

    # start rpc api server
    command_parser = subparsers.add_parser(
        "serve_api", help="Start RPC-API server."
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

    return vars(parser.parse_args(args=args)), parser
