#!/bin/bash

export FLASK_APP=./app/app.py
export FLASK_DEBUG=1

echo "Running GUNICORN ..."
gunicorn --bind 0.0.0.0:5000 app.app:app
