#!/usr/bin/env bash

cd /home/problemuser && sudo -H -u problemuser \
    /usr/bin/timeout -k 2 1800  /home/problemuser/chall
