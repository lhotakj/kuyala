#!/bin/bash

DOCKER_PWD=$(pwd)

cd ..

# here put your credentials or export manually

export SLACK_API_TOKEN=XXX
export VERIFICATION_TOKEN=XXXX
export LOG_FOLDER=/var/log/kratos-web

sudo docker build --file $OLDPWD/dockerfile \
                  --tag flask_gunicorn_app . \
                  --build-arg SLACK_API_TOKEN=$SLACK_API_TOKEN \
                  --build-arg VERIFICATION_TOKEN=$VERIFICATION_TOKEN
                  --build-arg LOG_FOLDER=$LOG_FOLDER

cd -