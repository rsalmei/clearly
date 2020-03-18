[![Travis](https://img.shields.io/travis/rsalmei/clearly.svg)]()
[![Coverage Status](https://coveralls.io/repos/github/rsalmei/clearly/badge.svg?branch=master)](https://coveralls.io/github/rsalmei/clearly?branch=master)
[![codecov](https://codecov.io/gh/rsalmei/clearly/branch/master/graph/badge.svg)](https://codecov.io/gh/rsalmei/clearly)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/rsalmei/clearly/graphs/commit-activity)
[![PyPI version](https://img.shields.io/pypi/v/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI status](https://img.shields.io/pypi/status/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI downloads](https://img.shields.io/pypi/dm/clearly.svg)](https://pypi.python.org/pypi/clearly/)


# clearly :)
## Clearly see and debug your celery pool in real time!

Do you use [celery](http://www.celeryproject.org), and monitor your tasks with [flower](https://github.com/mher/flower)? You'll probably like **Clearly**! 👍

`Clearly` is a real time monitor for your celery tasks and workers!

While I do like flower, to me it's not been totally up to the task (pun intended :).

Why is that? I'd like _actual_ real time monitoring, filter multiple task types at once, syntax coloring, and complete, whole, thorough, comprehensive results!

And guess what, `clearly` does provide all that! (and flower needs page refreshes, filters only one task type at a time, displays results as plain strings and on top of that also truncates them... :()

`Clearly` is actually real time, has multiple simultaneous filters, an advanced syntax coloring system, complete non-truncated results, shows parameters and results just as ipython would, and it's fast! :)
It's great to actually _see_ what's going on in your celery workers, and all in real time! So it's very nice for inspecting, debugging, and demonstrating your company async-superpowers (put `clearly` on a big TV showing all tasks of your production environment)!

`Clearly` is composed of an outer process server, which collects events from the celery pool, and a client, which you use to choose and filter what you want to see. They communicate with each other via gRPC and ProtocolBuffer.

See what `clearly` looks like:
![very cool](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_highlights.png)


## Requirements

To use `clearly`, you just have to:
- enable *Events* in your celery workers (`celery worker -E`)

and you're good to go!

Highlights:
- compatible with any version of celery, from 3.1 to 4.2+
- a result backend is not mandatory (but used if available)
- `clearly` supports python 3.5+ :)
(there's a version that still supports 2.7, see at the end of the page)


## Features

`clearly` enables you to:
- Be informed of any and all tasks beign handled, regardless of running, failing or just enqueued, in real time;
    - if you enable `task_send_sent_event` in your software, you can track tasks even before they’re consumed by a worker!
- Know the workers available and be notified immediately if any goes down or up;
- Filter the async tasks any way you want, both in real time and finished ones;
- Inspect the actual parameters the tasks were called with;
- See and analyze the outcome of these tasks, such as success results or fail tracebacks;
- _Clearly_ see all types and representations of the parameters/outcomes of the tasks with an advanced display system with syntax highlighting;
- Analyze stats of your system.


## Get `clearly` the docker way

```bash
$ docker pull rsalmei/clearly
```

The `clearly` image contains both the server and the client, so you should pull it in both machines.


### Start the server

```bash
$ docker run --rm -p <port>:12223 --name clearly-server \
      rsalmei/clearly server <broker_url> [--backend backend_url]
```


### Start the client

```bash
$ docker run --rm -ti --name clearly-client -v ipythonhist:/root/.ipython/profile_default/ \
      rsalmei/clearly client clearly-server

```

That's it, you're good to go!


<details>
<summary>Or get `clearly` the pip way</summary>

> ```bash
> $ pip install clearly
> ```
> 
> The `clearly` package contains both the server and the client, so you should install it in both machines.
> 
> 
> ### Start the server
> 
> ```bash
> $ clearly server <broker_url> [--backend backend_url] [--port 12223]
> ```
> 
> Use `clearly server --help` for more details.
> 
> <details>
> <summary>Just a quickie debug?</summary>
> 
> > _Clearly Client_ used to not need any server, which was convenient but made you lose all tasks' history once it is closed, and stresses the broker way more, as it must repeat all events to all connected clients.
> But if you'd like to use it quickly like that, be it to just assert something or to trial the framework before committing, you still can! Just start the server in-process:
> >
> > ```python
> > from clearly.server import start_server
> > server = start_server('<broker_url>')
> > ```
> >
> > Then you can simply start the client without arguments: `clearlycli = ClearlyClient()`
> </details>
> 
> 
> ### Start the client
> 
> Enter any REPL like python or IPython:
> 
> ```python
> from clearly.client import ClearlyClient
> clearlycli = ClearlyClient(host='<clearly_server>', port=<12223>)
> ```
> 
> That's it, you're good to go!
</details>


## How to use

So, you are ready to see tasks popping up in your screen faster than you can see?


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


> Note:
>
> Any way you capture them, remember that `clearly` server is always storing the same **complete data** about all your tasks! The `params` (and other related arguments) only configure how the client should display them to you.


### stop capturing and analyze
![useful results](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_results.png)


### get the big picture
![useful overview](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_brief.png)


## How `clearly` works

`Clearly` **server** creates a background thread with an events receiver, which captures them in real time directly from the broker, and dynamically updates their task's states.
It also has another thread to handle connected clients, dispatching events in real time to interested parties.

`Clearly` **client** can filter cached and real time tasks and workers, by type, routing key or task uuid, and get brief statistics about the `clearly` server.

The events may (and will) come in a chaotic order, so the server dynamically generates missing and ignores late ones, so you never see a STARTED task before it being RECEIVED, which would be weird. In a real time system this is very important, it's not about displaying the incoming state, but the inferred **current** state.

The parameters of the tasks are dynamically and safely compiled into an AST (_Abstract Syntax Tree_), and beautifully syntax colored. Completed tasks get their results directly from the result backend if available, to overcome the problem of truncated results (the broker messages have a size limit).

All async workers' life cycles are also processed and displayed, beautifully syntax colored too.
If you enable `task_send_sent_event`, all tasks triggered show up immediately on screen (it's quite nice!), and you start seeing what the workers are doing with them in real time!

At any moment, you can CTRL+C out of the capturing client, and rest assured the server continues to gather all updates seamlessly.

The memory consumption for server cached tasks, although very optimized, must of course be limited. By default it stores 10,000 tasks and 100 workers at a time, and is configurable:

```bash
  -t, --max_tasks INTEGER    Maximum number of tasks in memory
  -w, --max_workers INTEGER  Maximum number of workers in memory
```


### Architecture history

`Clearly` has started as a fully contained tool, one that you just start in a python REPL and filter tasks! It had connected directly to the broker, which had several shortcomings like stressing the broker (repeating **all events** to all connected `clearly`s), and losing all history whenever it is closed.

The architecture at that time had had two stages: one where it extracted events manually (which was hard, error prone and not forward compatible), and another with an event receiver directly from celery.

Nowadays, that event receiver is still here, but software architecture is quite different. Since version 0.5, it runs in a threaded `EventListener` processor, that captures raw celery events and updates their tasks in an LRU cache.

There's also a `StreamingDispatcher`, another threaded processor that maintains interested remote parties connected and shares task updates with them. For each new update, it tests whether each connected client would like to receive it, generating the missing states if they will (so it seems the events were perfectly ordered to the user).

Finally the `ClearlyServer` that encloses both, a gRPC server in a `ThreadPoolExecutor`, that accepts connections and handles to the streaming dispatcher (if a real time task capture was requested), or to the cache in event listener (for past tasks). And of course there's the `ClearlyClient`, which does not use any threads anymore and is totally broker and celery agnostic, relying only on the server via gRPC.


## API Reference

```python
def capture_tasks(pattern=None, negate=False, params=None, success=False, error=True):
    """Starts capturing task events in real time, so you can instantly see exactly
    what your publishers and workers are doing. Filter as much as you can to find
    what you need, and don't worry as the Clearly Server will still seamlessly
    handle all tasks updates.

    This runs in the foreground. Press CTRL+C at any time to stop it.

    Args:
        Filter args:
        ------------

        pattern (Optional[str]): a simple pattern to filter tasks by name.
            ex.: 'email' to filter task names containing that word anywhere
                 '^trigger|^email' to filter names starting with any of those words
                 'trigger.*123456' to filter names with those words in that sequence
        negate (bool): send True to filter tasks that do not match criteria.

        Display args:
        -------------

        params (Optional[bool]): if True shows args and kwargs in the first and
            last seen states, if False never shows, and if None follows the
            success and error arguments.
            default is None
        success (bool): if True shows successful tasks' results.
            default is False
        error (bool): if True shows failed and retried tasks' tracebacks.
            default is True, as you're monitoring to find errors, right?

    """
    return self.capture(pattern=pattern, negate=negate, workers='.', negate_workers=True,
                        params=params, success=success, error=error, stats=False)

def capture_workers(pattern=None, negate=False, stats=False):
    """Starts capturing worker events in real time, so you can instantly see exactly
    what your workers states are. Filter as much as you can to find
    what you need, and don't worry as the Clearly Server will still seamlessly
    handle all tasks and workers updates.

    This runs in the foreground. Press CTRL+C at any time to stop it.

    Args:
        Filter args:
        ------------

        pattern (Optional[str]): a simple pattern to filter workers by name.
            ex.: 'email' to filter worker names containing that word anywhere
                 'service|priority' to filter names containing any of those words
        negate (bool): send True to filter workers that do not match criteria.

        Display args:
        -------------

        stats (bool): if True shows complete workers' stats.
            default is False

    """
    return self.capture(pattern='.', negate=True, workers=pattern, negate_workers=negate,
                        params=False, success=False, error=False, stats=stats)

def capture(pattern=None, negate=False, workers=None, negate_workers=False,
            params=None, success=False, error=True, stats=False):
    """Starts capturing all events in real time, so you can instantly see exactly
    what your publishers and workers are doing. Filter as much as you can to find
    what you need, and don't worry as the Clearly Server will still seamlessly
    handle all tasks and workers updates.

    This runs in the foreground. Press CTRL+C at any time to stop it.

    See Also:
        capture_tasks()
        capture_workers()

    """


def stats():
    """Lists some metrics of the capturing system:

        Tasks processed: the total number of reentrant tasks processed,
            which includes retry attempts.
        Events processed: number of events captured and processed.
        Tasks stored: actual number of unique tasks processed.
        Workers stored: number of unique workers already seen.
    """


def tasks(pattern=None, negate=False, state=None, limit=None, reverse=True,
          params=None, success=False, error=True):
    """Filters stored tasks and displays their current statuses.

    Note that, to be able to list the tasks sorted chronologically, celery retrieves
    tasks from the LRU event heap instead of the dict storage, so the total number
    of tasks fetched may be different than the server `max_tasks` setting. For
    instance, the `limit` field refers to max events searched, not max tasks.

    Args:
        Filter args:
        ------------

        pattern (Optional[str]): a simple pattern to filter tasks by name.
            ex.: 'email' to filter task names containing that word anywhere
                 '^trigger|^email' to filter names starting with any of those words
                 'trigger.*123456' to filter names with those words in that sequence
        negate (bool): send True to filter tasks that do not match criteria.
        state (Optional[str]): a celery task state to filter
        limit (int): the maximum number of events to fetch
            if None or 0, fetches all.
        reverse (bool): if True (default), shows the most recent first

        Display args:
        -------------

        params (Optional[bool]): if True shows args and kwargs in the first and
            last seen states, if False never shows, and if None follows the
            success and error arguments.
            default is None
        success (bool): if True shows successful tasks' results.
            default is False
        error (bool): if True shows failed and retried tasks' tracebacks.
            default is True, as you're monitoring to find errors, right?

    """


def workers(pattern=None, negate=False, stats=True):
    """Filters known workers and prints their current status.
    
    Args:
        Filter args:
        ------------

        pattern (Optional[str]): a simple pattern to filter workers by name.
            ex.: 'email' to filter worker names containing that word anywhere
                 'service|priority' to filter names containing any of those words
        negate (bool): send True to filter workers that do not match criteria.

        Display args:
        -------------

        stats (bool): if True shows complete workers' stats.
            default is False

    """


def task(task_uuid):
    """Finds one specific task.

    Args:
        task_uuid (str): the task id
    """


def seen_tasks():
    """Shows a list of seen task types."""

def reset():
    """Resets all captured tasks."""
```


## Hints to extract the most of it

- write a small [celery router](http://docs.celeryproject.org/en/latest/userguide/routing.html#routers) and generate dynamic routing keys, based on the actual arguments of the async call in place! That way, you'll be able to filter tasks based on any of those, like an id of an entity. Remember the args and kwargs are not used in the filtering.
- if you're using [django](https://www.djangoproject.com/) and [django-extensions](https://github.com/django-extensions/django-extensions), put in your settings a `SHELL_PLUS_POST_IMPORT` to auto import `clearly`! Just create a module to initialize a `clearlycli` instance for the django `shell_plus` and you're good to go. It's really nice to have a tool always ready to be used, without importing or creating anything, to actually see what's going on in your tasks, even in production :)
- the more you filter, the less you'll have to analyze, so find the best combination for your debugging needs. A busy system can have thousands of tasks per minute, filter wisely.


## To do

- ~~support python 3;~~
- ~~split `Clearly` client and server, to allow an always-on server to run, with multiple clients connecting, without any of the shortcomings;~~
- ~~remove python 2 support~~
- ~~dockerize the server, to make its deploy way easier;~~
- include a script mode on client, to be able to call it right from the shell;
- any other ideas welcome!


## Changelog highlights:
- 0.8.1: keep un-truncate engine from breaking when very distant celery versions are used in publisher and server sides
- 0.8.0: clearly is dockerized! both server and client are now available in rsalmei/clearly docker hub; include new `capture_tasks` and `capture_workers` methods; fix task result being displayed in RETRY state; detect and break if can't connect to the broker
- 0.7.0: code cleanup, to support only Python 3
- 0.6.4: last version to support Python 2.7
- 0.6.0: supports again standalone mode, in addition to client/server mode
- 0.5.0: independent client and server, connected by gRPC (supports a server with multiple clients)
- 0.4.2: last version with client and server combined
- 0.4.0: supports both py2.7 and py3.4+
- 0.3.6: last version to support py2 only
- 0.3.0: result backend is not mandatory anymore
- 0.2.6: gets production quality
- 0.2.0: support standard celery events
- 0.1.4: last version that doesn't use events


### Python 2 has retired
That's why the support has been removed. For more details see https://pythonclock.org

To use in your python 2.7 projects, please use version 0.4.2 as in:

```bash
$ pip install clearly==0.4.2
```

This version is prior to the server split, so it connects directly to the broker, but works like a charm!

You could also use 0.6.4, which is newer, but please do mind that gRPC and Python itself have a very annoying bug in this case: you can't CTRL+C out of `clearly` client's `capture` method (or any streaming methods), so you have to kill the process itself when needed with CTRL+\\. For more details on this nasty bug:
- https://github.com/grpc/grpc/issues/3820
- https://github.com/grpc/grpc/issues/6999
- https://bugs.python.org/issue8844


## License
This software is licensed under the MIT License. See the LICENSE file in the top distribution directory for the full license text.


## Did you like it?

Thank you for your interest!

I've put much ❤️ and effort into this.

I wish you have fun using this tool! :)
