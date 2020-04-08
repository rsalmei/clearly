from celery import Celery

app = Celery('tasks', broker='amqp://localhost', backend='redis://localhost')
app.conf.task_send_sent_event = True
app.conf.task_serializer = 'pickle'  # to be able to demo all internal compiler goodies.
app.conf.accept_content = ['pickle']


@app.task(bind=True, max_retries=3)
def function_test(self, retries, **kwargs):
    if retries > self.request.retries:
        raise self.retry(countdown=2)
    return 'this is the result'


@app.task
def function_aggregate(*args, **kwargs):
    return dict(input=args, extra=kwargs)
