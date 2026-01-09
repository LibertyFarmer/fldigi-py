# fldigi-py

Modern Python client for FLDIGI XML-RPC (Python 3.7+)

## Install

pip install fldigi-py

## Quickstart

Start FLDIGI with XML-RPC:

fldigi --xmlrpc-server-address 127.0.0.1 --xmlrpc-server-port 7362

from fldigi_py import Fldigi

radio = Fldigi()
radio.add_tx("CQ TEST")
print(radio.frequency)  # 14074000.0
radio.mode = "PSK31"
print(radio.signal_strength)  # 85.3
