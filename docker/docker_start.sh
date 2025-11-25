#!/bin/bash
sudo docker run --detach -p 5000:5000 --name flask_gunicorn_app flask_gunicorn_app
echo "Starting app ... "

until [[ "$(curl --connect-timeout 10 -s -o /dev/null -w "%{http_code}" http://localhost:5000)" == "200" ]]
do
    echo "Waiting for the app starts ..."
    sleep 1
done
STATUS=$(curl --connect-timeout 10 -s -o /dev/null -w "%{http_code}" http://localhost:5000)
echo "App returned $STATUS"
