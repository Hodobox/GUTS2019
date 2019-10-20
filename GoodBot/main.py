#!/usr/bin/python3

import json
import socket
import logging
import binascii
import struct
import argparse
import random
import pickle
from bot import Bot
from serverComms import *
import threading
from State import *

# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='IfBot:', help='Name of bot')

args = parser.parse_args()

# Set up console logging
if args.debug:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)

NUMBOTS = 4

# Connect to game server
state = State()
botnames = ['0','1','2','3']
ports = [8052,8052,8052,8052]
servers = [ ServerComms(args.hostname,ports[i]) for i in range(NUMBOTS) ]
bots = [ Bot(i,args.name + botnames[i], servers[i], ports[i], state) for i in range(NUMBOTS) ]

for i in range(NUMBOTS):
    x = threading.Thread(target=bots[i].activate)
    x.start()
