#!/bin/bash

set -e

#The script gets called with tag that could be either prod  or staging
Tag=$1

echo $Tag

echo kashaglobal/jazaduka:"$Tag"

cd /home/robot/jaza/jazaduka

echo Pulling Docker image for deployment

docker pull kashaglobal/jazaduka:"$Tag"

echo 'Pull done stopping running containers'
docker-compose -f production.yml stop

echo 'Running migrations'
docker-compose -f production.yml run --rm django python manage.py migrate

echo 'Restarting the containers'
docker-compose -f production.yml up -d

echo 'Remove old unused containers'
docker container prune -f
