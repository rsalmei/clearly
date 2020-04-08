import time

from celery import chord, group

from .worker import function_aggregate, function_test

chord(
    group(function_test.s(0, value=i) for i in range(1000)),
    function_aggregate.s(from_chord=True)
)()

time.sleep(5)
