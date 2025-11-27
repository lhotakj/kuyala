#!/bin/bash
PYTHON3=python3

sudo $PYTHON3 -m pip install virtualenv
virtualenv "kuyala"
source kuyala/bin/activate

$PYTHON3 -m pip install gunicorn flask
