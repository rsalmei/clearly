[![Travis](https://img.shields.io/travis/rsalmei/clearly.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-100%25-green.svg)]()
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/rsalmei/clearly/graphs/commit-activity)
[![PyPI version](https://img.shields.io/pypi/v/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI status](https://img.shields.io/pypi/status/clearly.svg)](https://pypi.python.org/pypi/clearly/)


# clearly :)
## Clear and accurate real-time monitor for celery

Do you use [celery](http://www.celeryproject.org), and monitor your tasks with [flower](https://github.com/mher/flower)? You'll probably like **Clearly**!

`Clearly` is a real-time monitor for your celery tasks and workers!

While I do like flower, to me it's not been totally up to the task (pun intended :)).
Why is that? I'd like _actual_ real-time monitoring, filter multiple tasks at once, syntax coloring, and complete, whole, thorough, comprehensive results!
And flower needs page refreshes, filters only one task at a time, displays results as plain strings, and even truncates them... :(

Ok, `clearly` does provide all that!  
It is actually real-time, has multiple simultaneous filters, an advanced syntax coloring system, complete non-truncated results, and it's fast! :)
It's great to actually _see_ what's going on in your celery workers, all in real-time! So it's great for inspecting, debugging, and demonstrating your company async-superpowers (put `clearly` on a big TV)!

`Clearly` has an outer process server, and the clients connect to it via gRPC.
This makes `clearly` quite complete, and could even substitute flower entirely for monitoring needs.

It's only missing a Docker image for simple deploying now.
And a command line to call the client directly from the shell!
(spoilers :))

See what `clearly` looks like:
![very cool](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_highlights.png)


## Requirements

To use `clearly`, you just have to:
- enable *Events* (`celery worker -E`)

and you're good to go!

Highlights:
- compatible with any version of celery, from 3.1 to 4.2+
- a result backend is not mandatory (but used if available)
- `clearly` supports both python 2.7 and python 3.5+ :)


## How `clearly` works

`Clearly` is composed of a server and a client.
The server creates a background thread with a celery events receiver, which captures events from all publishers and all workers connected, dynamically updating states.
It also has another thread to handle connected clients, dispatching events in real-time to interested parties.
The client(s) can also filter stored tasks and workers, find a specific task uuid, or get brief statistics about the server.

The events are processed in the server, and missing or out of order ones are dynamically generated, so you never see a STARTED task before it being RECEIVED, which would be weird. In a real-time system this is important, as it's not just displaying the current state.

The parameters of the tasks are dynamically (and safely) compiled into an _Abstract Syntax Tree_, and beautifully syntax colored, while completed tasks get their results directly from the result backend if available, to overcome the problem of truncated results.
All async workers' life cycles are also processed and displayed on screen (beautifully syntax colored too, of course).
All tasks triggered show up immediately on screen, and you start seeing what the workers are doing with them in real-time!

At any moment, you can CTRL+C out of the capturing client, and rest assured that there's a server out there, which continues to gather all updates seamlessly.

The memory consumption, although very optimized, must of course be limited. By default it stores 10,000 tasks and 100 workers at a time. You can increase them (or decrease) if you want.


### Architecture history

`Clearly` has started as a fully contained tool, one that you just start anywhere and see events. The client has always connected directly to the broker, but it had two stages: one where it extracted events manually, and another with an actual event receiver from celery.

The software architecture is quite different now, since 0.5. It has a threaded `EventListener` that captures raw celery events, storing them in the default LRU memory, and converting to an immutable format before passing up to the next phase via a Queue.

Then there's the `StreamingDispatcher`, another threaded processor, that maintains interested parties and shares events with them. For each new event, it tests whether a connected client would like to see it, and if yes it generates the missing gaps in states and sends them to a client specific Queue.

Finally there's the new `ClearlyServer`, a gRPC server in a `ThreadPoolExecutor`, that accepts connections and handles to: the streaming dispatcher if a real-time capture was requested, or to the listener memory for already persisted events. And of course there is the new `ClearlyClient`, which does not use threads anymore or any server resources like the broker or celery app, instead it uses a stub to connect to the server host:port via gRPC.


## Features

`clearly` enables you to:
- Be informed of any and all tasks being triggered and running and failing, in real-time;
- Know the workers available and be notified immediately if any goes down or up;
- Filter the async tasks any way you want, real-time and finished alike;
- Inspect the actual parameters the tasks were called with;
- See and analyze the outcome of these tasks, such as success results or fail tracebacks;
- _Clearly_ see all types and representations of the parameters/outcomes of the tasks with an advanced printing system and syntax highlighting;
- Analyze stats of your system.


## Get `clearly`

Just do in your python env:

```bash
$ pip install clearly
```


## How to use

### start the server

Basically just do:

```bash
$ clearly server <broker_url> [--backend backend_url] [--port 12223]
```

Use `clearly --help` and `clearly server --help` for more options.


#### Can't/won't install the server yet?

_Clearly Client_ used to be started without any server, which was convenient, but made you lose all tasks' history when you close it. If you'd like to use it quickly like that, be it to just assert something or to trial the software before committing, just do this:

```python
>>> from clearly.server import start_server
>>> server = start_server('your_broker_url')
```

Then you'll be able to use the client as below, pointing it to `localhost`!


### start the client ([i]python)

```python
>>> from clearly.client import ClearlyClient
>>> clearlycli = ClearlyClient(host='hostname', port=12223)
```


### grab them

```python
>>> clearlycli.capture()
```


### be amazed
![very amazed](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_amazed.png)


### you can also grab like

```python
>>> clearlycli.capture(params=True)
```


### and also be amazed
![very amazed](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_cool.png)


### note

Any way you capture them, `clearly` server is always storing the same complete data about the tasks. The `params` (and other arguments) are only display related, for you to see the events the way you want, both in capture and stored modes.
(The default is to show `error`s, as they are much more likely to get your interest).


### stop capturing and analyze
![useful results](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_results.png)


### get the big picture
![useful overview](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_brief.png)


## API Reference

```python
def capture(self, pattern=None, negate=False, workers=None, negate_workers=False,
            params=None, success=False, error=True, stats=False):
    """Starts capturing selected events in real-time. You can filter exactly what
    you want to see, as the Clearly Server handles all tasks and workers updates
    being sent to celery. Several clients can see different sets of events at the
    same time.

    This runs in the foreground, so you can see in real-time exactly what your
    celery workers are doing.
    Press CTRL+C at any time to stop it.

    Args:
        Filter args:

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

        Display args:

        success (bool): if True shows successful tasks' results.
            default is False
        error (bool): if True shows failed and retried tasks' tracebacks.
            default is True, as you're monitoring to find errors, right?
        stats (bool): if True shows complete workers' stats.
            default is False
    """


def stats(self):
    """Lists some metrics of the capturing system:

        Tasks processed: the total number of reentrant tasks processed,
            which includes retry attempts.
        Events processed: number of events captured and processed.
        Tasks stored: actual number of unique tasks processed.
        Workers stored: number of unique workers already seen.
    """


def tasks(self, pattern=None, negate=False, state=None, limit=None, reverse=True,
          params=None, success=False, error=True):
    """Filters stored tasks and prints their current status.

    Note that, in the server, to be able to list the tasks sorted chronologically,
    they are retrieved from the LRU heap instead of the dict storage, so the total
    number of tasks fetched may be different than the server `max_tasks` setting.

    Args:
        Filter args:

        pattern (Optional[str]): a pattern to filter tasks
            ex.: '^dispatch|^email' to filter names starting with those
                  or 'dispatch.*123456' to filter that exact name and number
                  or even '123456' to filter that exact number anywhere.
        negate (bool): if True, finds tasks that do not match criteria
        state (Optional[str]): a state to filter tasks
        limit (int): the maximum number of tasks to fetch
            if None or 0, fetches all.
        reverse (bool): if True (default), shows the most recent first

        Display args:

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
        Filter args:

        pattern (Optional[str]): a pattern to filter workers
            ex.: '^dispatch|^email' to filter names starting with those
                  or 'dispatch.*123456' to filter that exact name and number
                  or even '123456' to filter that exact number anywhere.
        negate (bool): if True, finds tasks that do not match criteria

        Display args:

        stats (bool): if True shows worker stats
    """


def task(self, task_uuid):
    """Finds one specific task.

    Args:
        task_uuid (str): the task id
    """


def seen_tasks(self):
    """Shows a list of seen task types."""

def reset(self):
    """Resets all captured tasks."""
```


## Hints

- write a small [celery router](http://docs.celeryproject.org/en/latest/userguide/routing.html#routers) and generate dynamic routing keys, based on the actual arguments of the async call in place. That way, you'll be able to filter tasks based on any of those, like an id of an entity. The args and kwargs are not used in the filtering.
- if you're using [django](https://www.djangoproject.com/) and [django-extensions](https://github.com/django-extensions/django-extensions), put in your settings a `SHELL_PLUS_POST_IMPORT` to auto import `clearly`! Just create a module to initialize a `clearlycli` instance for the django `shell_plus` and you're good to go. It's really nice to have a tool always ready to be used, without importing or creating anything, to actually see what's going on in your tasks, even in production :)
- the more you filter, the less you'll have to analyze, so find the best combination for you debugging needs. A busy system can have thousands of tasks per minute.


## To do

- ~~support python 3 (not actually tested yet, soon);~~
- ~~split `Clearly` client and server, to allow a always-on server to run, and multiple clients connect;~~
- include a script mode, to call right from the shell;
- any other ideas welcome!


## Changelog highlights:
- 0.6.0: supports again standalone mode, in addition to client/server mode
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


## Nice huh?

Thanks for your interest!

I wish you have fun using this tool! :)
