[![Travis](https://img.shields.io/travis/rsalmei/clearly.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-100%25-green.svg)]()
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/rsalmei/clearly/graphs/commit-activity)
[![PyPI version](https://img.shields.io/pypi/v/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI status](https://img.shields.io/pypi/status/clearly.svg)](https://pypi.python.org/pypi/clearly/)


# clearly :)
## Clear and accurate real-time monitor for celery

`Clearly` is an alternative to [flower](https://github.com/mher/flower).
While I do like flower, to me it's not been totally up to the task (pun intended :)).
Why is that? I'd like _actual_ real-time monitoring, filter multiple tasks at once, syntax coloring and complete, whole, thorough, comprehensive results!
And flower needs page refreshes, filters only one task at a time, displays results as plain strings and on top of that truncates them... 😞

Ok, `clearly` does provide all that!  
It is actual real-time, has multiple simultaneous filters, an advanced syntax coloring system, and complete non-truncated results! Oh, and it works right in the (i)python terminal :)
It's great to actually _see_ what's going on in your celery tasks, all in real-time! So it's great for debugging and demoing.

Now, `clearly` even has an outer process server!
You can always connect to it, and see the last 10,000 tasks, anytime.
This makes `clearly` quite complete, and can even substitute flower entirely.

It's only missing a Docker image for simple deploying now.
And a command line to call the client directly from the shell!
(spoilers :))

See what `clearly` looks like:
![very cool](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_highlights.png)


## Requirements

To use `clearly`, you currently need to:
- enable *Events* (`celery worker -E`)

and you're good to go!

Highlights:
- any version of celery will work, from 3.1 to 4.2+ :)
- a result backend is not mandatory (but used if available :)
- now the code supports both python 2.7 and python 3.5+ :)


## How `clearly` works

`Clearly` is composed of a server and a client.
The server creates a background thread with a celery events receiver, which receives events from all publishers and all workers connected, dynamically updating states.
It also has another thread to handle connected clients, dispatching events in real-time to interested parties.
The client(s) can also filter stored tasks and workers, find a specific task uuid, or get statistics about the cluster.

Those events are processed in the server, and missing or out of order ones are dynamically generated, so you never see a STARTED task before it being RECEIVED, which would be weird.
The parameters of the tasks are dynamically (and safely) compiled, and beautifully syntax colored, while tasks completed get their results directly from the result backend if available, to overcome the problem of truncated results.
All async workers' life cycles are also processed and listed on screen (beautifully syntax colored, of course).
All tasks triggered show up immediately on screen, and you start seeing what the workers are doing with them in real-time!

At any moment, you can CTRL+C out of the client, and rest assured that there's a server out there, which will continue gathering all updates seamlessly.

The memory consumption, although very optimized, must of course be limited. By default it stores 10,000 tasks and 100 workers at a time. You can increase them if you want.


## Features

`clearly` enables you to:
- Be informed of any and all tasks being requested and running, in real-time;
- Know the workers available and be notified if any goes down;
- Filter the async calls any way you want;
- Inspect the actual parameters the tasks were called with;
- See and analyze the outcome of these tasks, such as success results or fail tracebacks;
- _Clearly_ see all types and representations of the parameters/outcomes of the tasks with an advanced printing system, syntax highlighting and symbols, similar to what your favorite REPL would do;
- Analyze stats of your system.


## Get `clearly`

1. `pip install -U clearly`
2. that's all!


## How to use

### start the server (bash)

```bash
>>> clearly server <broker_url> [--backend backend_url] [--port 12223]

>>> clearly --help
Usage: clearly [OPTIONS] COMMAND [ARGS]...

Options:
  --version             Show the version and exit.
  --debug / --no-debug  Enables debug logging
  --help                Show this message and exit.

Commands:
  server

>>> clearly server --help
Usage: clearly server [OPTIONS] BROKER

Options:
  --backend TEXT  Enables complete task results from result backend
  --port INTEGER  Listen port for Clearly
  --help          Show this message and exit.
```

### start the client ([i]python)

```python
>>> from clearly.client import ClearlyClient
>>> clearlycli = ClearlyClient(host='hostname', port=12223)
```

### grab them

```python
clearlycli.capture()
```


### be amazed
![very amazed](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_amazed.png)


### you can also grab like

```python
clearlycli.capture(params=True)
```


### and also be amazed
![very amazed](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_cool.png)


### note
Any way you capture them, `clearly` is always storing the same data about the tasks. The `params` is only informative, for you to see them right in the capture mode. You can see them later too, after capturing.
(The default is to show `error`s, as they are much more likely to get your interest).


### stop capturing and analyze
![useful results](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_results.png)


### get the big picture
![useful overview](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_brief.png)


## API Reference

```python
def capture(self, pattern=None, negate=False, workers=None, negate_workers=False,
            params=None, success=False, error=True, stats=False):
    """Starts the real-time engine that captures events. It will capture
    all tasks being sent to celery and all workers known to it.

    This will be run in the foreground, so you can see in real-time
    exactly what your celery workers are doing.
    You can press CTRL+C at any time to stop it, without losing any
    updates, which are still being captured in the background.
    
    Args:
        pattern (Optional[str]): a pattern to filter tasks to capture.
            ex.: '^dispatch|^email' to filter names starting with that
                  or 'dispatch.*123456' to filter that exact name and number
                  or even '123456' to filter that exact number anywhere.
        negate (bool): if True, finds tasks that do not match criteria.
        workers (Optional[str]): a pattern to filter workers to capture.
            ex.: 'service|priority' to filter names containing that
        negate_workers (bool): if True, finds workers that do not match criteria.
        params (Optional[bool]): if True shows args and kwargs in first/last state,
            doesn't show if False, and follows the successes and errors if None.
            default is None
        success (bool): if True shows successful tasks' results.
            default is False
        error (bool): if True shows failed and retried tasks' tracebacks.
            default is True, as you're monitoring to find errors, right?
        stats (bool): if True shows complete workers' stats.
            default is False
    """


def stats(self):
    """Lists some metrics of your actual and capturing system.
    Those are:
        Tasks processed: the total number of reentrant tasks processed,
            which includes retry attempts.
        Events processed: number of events captured and processed.
        Tasks stored: actual number of unique tasks processed.
        Workers stored: number of unique workers already seen.
    """


def tasks(self, pattern=None, negate=False, state=None,
          params=None, success=False, error=True):
    """Filters stored tasks and prints their current status.
    There are a few params with different defaults from the equivalent
    capture method. This is because here we have more info about the tasks,
    and so it can use new tricks.
    
    Args:
        pattern (Optional[str]): a pattern to filter tasks
            ex.: '^dispatch|^email' to filter names starting with those
                  or 'dispatch.*123456' to filter that exact name and number
                  or even '123456' to filter that exact number anywhere.
        negate (bool): if True, finds tasks that do not match criteria
        state (Optional[str]): a state to filter tasks
        params (Optional[bool]): if True shows called args and kwargs,
            skips if False, and follows outcome if None.
            default is None
        success (bool): if True shows successful tasks' results
            default is False
        error (bool): if True shows failed and retried tasks' tracebacks.
            default is True, as you're monitoring to find errors, right?
    """


def workers(self, pattern=None, negate=False, stats=True):
    """Filters known workers and prints their current status.
    
    Args:
        pattern (Optional[str]): a pattern to filter workers
            ex.: '^dispatch|^email' to filter names starting with those
                  or 'dispatch.*123456' to filter that exact name and number
                  or even '123456' to filter that exact number anywhere.
        negate (bool): if True, finds tasks that do not match criteria
        stats (bool): if True shows worker stats
    """


def task(self, task_uuid):
    """Shows one specific task.

    Args:
        task_uuid (str): the task id
    """


def seen_tasks(self):
    """Shows a list of task types seen."""


def reset(self):
    """Resets all captured tasks."""
```


## Hints

- write a small [celery router](http://docs.celeryproject.org/en/latest/userguide/routing.html#routers) and in there generate dynamic routing keys, based on the actual arguments of the async call in place.
That way, you'll be able to filter tasks based on any of those constraints, like an id of an entity.
- if you're using [django](https://www.djangoproject.com/) and [django-extensions](https://github.com/django-extensions/django-extensions), put in your settings a `SHELL_PLUS_POST_IMPORT` to auto import this!
Just create a module to initialize a `clearlycli` instance and you're good to go, the shell_plus will have it always available!
Now you have a tool always ready to be used, without importing or creating anything, to actually see what's going on in your tasks, even in production :)
(soon there will be a command line to get even easier to this)
- the more you filter, the less you'll have to analyze, so find the best combination for you debugging needs. A busy system can have thousands of tasks per minute.


## To do

- ~~support python 3 (not actually tested yet, soon);~~
- ~~split `Clearly` client and server, to allow a always-on server to run, and multiple clients connect;~~
- include a script mode, to call right from the shell;
- any other ideas welcome!


## Changelog highlights:
- 0.5.0: independent client and server, connected by gRPC (supports a server with multiple clients)
- 0.4.2: last version with client and server combined
- 0.4.0: supports both py2.7 and py3.4+
- 0.3.6: last version to support py2 only
- 0.3.0: result backend is not mandatory anymore
- 0.2.6: gets production quality
- 0.2.0: support standard celery events
- 0.1.4: last version that doesn't use events


## License
This software is licensed under the MIT License. See the LICENSE file in the top distribution directory for the full license text.

## Thank you.
