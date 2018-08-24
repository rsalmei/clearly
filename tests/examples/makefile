
setup:
	docker run -d -p 6379:6379 --rm --name redishost redis:alpine
	docker run -d -p 5672:5672 -p 15672:15672 --rm --name rabbithost rabbitmq:management-alpine

worker:
	celery worker -A tasks -E --loglevel=info --heartbeat-interval 10 $(args)

server:
	clearly --debug server amqp://localhost

sender:
	ipython sender.py

isender:
	ipython -i sender.py

client:
	ipython client.py

iclient:
	ipython -i client.py
