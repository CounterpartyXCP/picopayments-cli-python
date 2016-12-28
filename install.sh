#!/usr/bin/env bash
sudo apt-get install python3-pip
pip3 install picopayments-cli
sed 's/5d/"hub_verify_ssl_cert": false/g' ~/.picopayments/testnet.cfg

