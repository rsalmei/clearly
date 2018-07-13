from celery import chord, group
from tasks import *

chord(group(function_value.s(0, value=i) for i in range(30)), function_any.s(from_chord=True))()
