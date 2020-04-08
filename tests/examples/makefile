.PHONY: all setup worker server client sender

all:
	@grep -E "^\w+:" makefile | cut -d: -f1

setup:
	docker-compose up -d rabbithost redishost

server-backend: ARGS=--backend redis://redishost
server-backend: server

server:
	docker-compose run --rm --name clearly-server clearly-service \
	    server --debug amqp://rabbithost $(ARGS)
# 	docker run --rm -p 12223:12223 --name clearly-server -v $(shell pwd)/../../:/usr/src/clearly \
	    --network examples_default \
	    rsalmei/clearly server --debug amqp://rabbithost $(ARGS)

client:
	docker-compose run --rm --name clearly-client -e CLI_DISPLAY_MODES="7 13" clearly-service \
	    client clearly-server
# 	docker run --rm -ti --name clearly-client -v $(shell pwd)/../../:/usr/src/clearly \
	    --network examples_default -v ipythonhist:/root/.ipython/profile_default/ \
	    rsalmei/clearly client clearly-server $(ARGS)

worker:
	docker-compose run --rm --name worker user-app \
	    celery worker -A user_code.worker -E --loglevel=info --heartbeat-interval 60

publisher-group:
	docker-compose run --rm --name publisher user-app \
	    ipython -m user_code.publisher_group

publisher-demo:
	docker-compose run --rm --name publisher user-app \
    	ipython -m user_code.publisher_demo
