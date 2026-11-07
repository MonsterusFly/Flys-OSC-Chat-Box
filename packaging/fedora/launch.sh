#!/bin/sh
set -eu
cd /usr/share/flys-osc-chat-box
exec /usr/bin/python3 /usr/share/flys-osc-chat-box/main.py "$@"
