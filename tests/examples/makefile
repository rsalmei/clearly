.PHONY: all setup worker server client sender

all:
	@grep -E "^\w+:" makefile | cut -d: -f1

setup:
	docker-compose up -d rabbithost redishost

server-backend: ARGS=--backend redis://redishost
server-backend: server

server:
	docker-compose run --rm --name clearly-server clearly-service server --debug amqp://rabbithost $(ARGS)
# 	docker run --rm -p 12223:12223 --name clearly-server -v $(shell pwd)/../../:/usr/src/clearly \
	    --network examples_default \
	    rsalmei/clearly server --debug amqp://rabbithost $(ARGS)

client:
	docker-compose run --rm --name clearly-client clearly-service client clearly-server
# 	docker run --rm -ti --name clearly-client -v $(shell pwd)/../../:/usr/src/clearly \
	    --network examples_default -v ipythonhist:/root/.ipython/profile_default/ \
	    rsalmei/clearly client clearly-server $(ARGS)

worker:
	celery worker -A user_code.tasks -E --loglevel=info --heartbeat-interval 10 $(ARGS)

publisher:
	ipython -m user_code.publisher

ipublisher:
	ipython -mi user_code.publisher
