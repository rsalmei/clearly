from celery import Celery

app = Celery('tasks', broker='amqp://localhost', backend='redis://localhost')


@app.task(bind=True)
def function_value(self, retries, **kwargs):
    if retries > self.request.retries:
        raise self.retry(countdown=0, exc='retry-{}'.format(self.request.retries))
    return kwargs.get('value', -1)


@app.task(bind=True)
def function_kwargs(self, retries, **kwargs):
    if retries > self.request.retries:
        raise self.retry(countdown=0, exc='retry-{}'.format(self.request.retries))
    return kwargs


@app.task(bind=True)
def function_none(self, retries, **kwargs):
    if retries > self.request.retries:
        raise self.retry(countdown=0, exc='retry-{}'.format(self.request.retries))
