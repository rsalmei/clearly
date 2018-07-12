#!/usr/bin/env bash

docker run -d -p 6379:6379 --rm --name redishost redis:alpine
docker run -d -p 5672:5672 -p 15672:15672 --rm --name rabbithost rabbitmq:management-alpine
