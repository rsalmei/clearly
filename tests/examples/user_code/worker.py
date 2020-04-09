from celery import Celery

app = Celery('tasks', broker='amqp://rabbithost', backend='redis://redishost')
app.conf.task_send_sent_event = True
app.conf.task_serializer = 'pickle'  # to be able to demo all internal compiler goodies.
app.conf.accept_content = ['pickle', 'json']  # apparently canvas workflow are always json.
app.conf.resultrepr_maxsize = 100 * 1024  # to not truncate args and kwargs until that size.
# unfortunately it is not working, as of 4.4.2
# http://docs.celeryproject.org/en/latest/reference/celery.app.task.html#celery.app.task.Task.resultrepr_maxsize


@app.task(bind=True, max_retries=2)
def function_test(self, retries, **kwargs):
    if retries > self.request.retries:
        raise self.retry(countdown=1)
    return kwargs.get('result', 'this is the result')


@app.task
def function_aggregate(*args, **kwargs):
    return dict(input=args, extra=kwargs)
