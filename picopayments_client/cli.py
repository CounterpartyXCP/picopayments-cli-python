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

    # network to use
    parser.add_argument(
        '--testnet', action='store_true', help="Use bitcoin testnet."
    )

    # logging options
    parser.add_argument(
        '--debug', action='store_true', help="Maximum logging."
    )
    parser.add_argument(
        '--verbose', action='store_true', help="Maximum logging."
    )
    parser.add_argument(
        '--quite', action='store_true', help="Minimum logging."
    )

    # show version
    parser.add_argument(
        '--version', action='store_true', help="Show version number."
    )

    # show hub terms
    parser.add_argument(
        '--terms', action='store_true', help="Show hub terms."
    )

    # basedir path
    default = os.path.join(os.path.expanduser("~"), ".picopayments")
    parser.add_argument(
        '--basedir', default=default, metavar="PATH",
        help="Location of app files: {0}".format(default)
    )

    # serve rpc api
    parser.add_argument(
        '--api-serve', action='store_true', help="Start RPC-API server."
    )
    parser.add_argument(
        '--api-host', default="localhost", metavar="PORT",
        help="RPC-API server host: {0}".format("localhost")
    )
    default = 15000 if testnet else 5000
    parser.add_argument(
        '--api-port', type=int, default=default, metavar="PORT",
        help="RPC-API server port: {0}".format(default)
    )

    # commands

    # picopayments hub
    default_port = 14000 if testnet else 4000
    default = "http://public.coindaddy.io:{0}/api/".format(default_port)
    parser.add_argument(
        '--hub-url', default=default, metavar="URL",
        help="Counterparty api: {0}".format(default)
    )
    parser.add_argument(
        '--hub-username', default="rpc", metavar="VALUE",
        help="Counterparty username: {0}".format("rpc")
    )
    parser.add_argument(
        '--hub-password', default="1234", metavar="VALUE",
        help="Counterparty password: {0}".format("1234")
    )

    # generic options
    parser.add_argument(
        '--handle', default=None, metavar="HANDLE",
        help="Filter result by connection handle."
    )
    parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="Filter result by asset."
    )
    parser.add_argument(
        '--quantity', default=None, metavar="HANDLE",
        help="Filter result by connection handle."
    )

    # filter state
    parser.add_argument(
        '--connecting', action='store_true',
        help="Filter result open connections."
    )
    parser.add_argument(
        '--open', action='store_true',
        help="Filter result open connections."
    )
    parser.add_argument(
        '--closed', action='store_true',
        help="Filter result open connections."
    )

    return vars(parser.parse_args(args=args))
