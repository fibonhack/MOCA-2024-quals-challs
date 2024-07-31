#!/usr/bin/env bash

cd /home/problemuser && sudo -H -u problemuser \
    /usr/bin/timeout -k 2 60 /usr/bin/python3 /home/problemuser/chall.py
