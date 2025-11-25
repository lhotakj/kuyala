#!/bin/bash
export FLASK_APP=app/app.py
export FLASK_ENV=development
export KUBECONFIG="~/.kube/config"
flask run --reload --host=0.0.0.0