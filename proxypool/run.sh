#!/bin/bash

# install dependencies
pip3 install -r requirements.txt

# download_nodes
python proxyPool.py --download --file public_nodes.yaml


