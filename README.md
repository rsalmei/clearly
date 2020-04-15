[<img align="right" src="https://cdn.buymeacoffee.com/buttons/default-orange.png" width="217px" height="51x">](https://www.buymeacoffee.com/rsalmei)

![Clearly logo](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_logo_small.png)

## Clearly see and debug your celery cluster in real time!

[![Travis](https://img.shields.io/travis/rsalmei/clearly.svg)]()
[![Coverage Status](https://coveralls.io/repos/github/rsalmei/clearly/badge.svg?branch=master)](https://coveralls.io/github/rsalmei/clearly?branch=master)
[![codecov](https://codecov.io/gh/rsalmei/clearly/branch/master/graph/badge.svg)](https://codecov.io/gh/rsalmei/clearly)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/rsalmei/clearly/graphs/commit-activity)
[![PyPI version](https://img.shields.io/pypi/v/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI status](https://img.shields.io/pypi/status/clearly.svg)](https://pypi.python.org/pypi/clearly/)
[![PyPI downloads](https://img.shields.io/pypi/dm/clearly.svg)](https://pypi.python.org/pypi/clearly/)


Do you use [celery](http://www.celeryproject.org), and monitor your tasks with [flower](https://github.com/mher/flower)? You'll probably like **Clearly**! 👍

#### `Clearly` is a **real time** monitor for your celery tasks and workers!

While I do like _flower_, to me it's not been totally up to the task (pun intended :).
<br>Why is that? _flower_ needs page refreshes, filters only one task type at a time, displays results as plain strings without any formatting or syntax highlighting, and on top of that also truncates them!

And `clearly` is _actually_ real time, has multiple simultaneous filters, a beautiful syntax highlighting system, an advanced formating system that shows parameters, results and tracebacks just as an ipython would, has complete un-truncated results and is very easy to use! 😃
<br>Also you can install it very easily with a docker image!

It's great to actually see in a totally _real time way_ what's going on in your celery workers! So it's very nice for inspecting, debugging, and even demonstrating your company async-superpowers (put `clearly` on a big screen TV showing all tasks of your production environment 😜)!

`Clearly` is composed of a server, which collects real time events from the celery cluster, generates missing states, and streams filtered data to connected clients; and a client, which you use to send filter commands and display both real time and stored data. They communicate with each other via gRPC and ProtocolBuffers.

See what `clearly` looks like:
![very cool](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_highlights.png)


> ### 📌 New version!
> 
> **Clearly** has received a major revamp in version 0.9, since its very near 1.0! \o/
> 
> All code has been revisited and several new features were implemented, which took ~170 commits, ~70 files changed and ~2700 additions! `Clearly` is now more mature, more reliable and way more polished in general, with beautiful colors and complete error handling, making this new `Clearly` way more pleasant to use!
>
> And there's also the unit tests, which were greatly streamlined. The suite has gone from ~2600 tests down to less than 700, while keeping 100% code coverage (branch-coverage)! The _PR_ is in https://github.com/rsalmei/clearly/pull/52 if you'd like to see it.
> 
> This endeavor has taken five weeks of full-time work, and demanded a great effort. If you appreciate my work, you could buy me a coffee 😊, I would really appreciate that! _(the button is on the top-right corner)_
> 
> Also please help `Clearly` gain more momentum! Tweet about it, write a blog post about it or just recommend it!
>
> Enjoy!

---

## Features

`Clearly` enables you to:
- Be informed of any and all tasks running, failing or just being enqueued, both in real time and stored;
    - if you enable `task_send_sent_event` in your code, you can track tasks even before they get into a worker!
- Be informed of workers availability, knowing immediately if any goes down or up;
- Filter tasks any way you want by several fields, both in real time and stored;
- Debug the actual parameters the tasks were called with, and analyze their outcome, such as success results or failure tracebacks and retries;
- All types and representations of those parameters and outcomes can be _clearly_ seen with the advanced formatting system and syntax highlighting;
- Analyze metrics of your system.


#### `Clearly` is

- compatible with any version of celery, from 3.1 to 4.4+;
- aware of your result backend, using it if available to retrieve tasks' results;
- running inside docker, so anyone with any version of python can use it! 👏


#### `Clearly` is not

- an administration tool for celery clusters, it is specialized in monitoring.

---

## Get `clearly` the docker way

### Requirements

To use `clearly`, you just have to:
- enable *Events* in your celery workers (`celery worker -E`)

and you're good to go!


### Start the server

```bash
$ docker run --rm --name clearly-server -p <clearly_port>:12223 \
      rsalmei/clearly server <broker_url> [--backend backend_url]
```

You should see something like:

![server](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_server.png)


### Start the client

```bash
$ docker run --rm -ti --name clearly-client -v ipythonhist:/root/.ipython/profile_default/ \
      rsalmei/clearly client [clearly_server [clearly_port]]
```

> Note: The above volume (`-v`) is not really necessary, but it's very nice to not lose your `clearlycli` history every time you leave it. I recommend it 👍.

That's it, you're good to go! \o/


<details>
<summary>What, you really need to use it inside your own REPL?</summary>

> Ok, you can use `clearly` the pip way, but this is not recommended anymore. The docker way is much more portable, and avoids coupling between yours and `clearly` code. Also enables me to use internally any python version I see fit, without fear of breaking user's code.
> See in the changelog the currently supported python version.
>
> ```bash
> $ pip install clearly
> ```
> 
> ### Start the server
> 
> ```bash
> $ clearly server <broker_url> [--backend backend_url] [--port 12223]
> ```
>
> <details>
> <summary>Just a quickie debug?</summary>
>
> > _Clearly Client_ used to not need any server, which was convenient but had several shortcomings, like losing all history when closed, and receiving every single event from the celery cluster for each new client, which stressed the broker way more.
> But if you'd like to use it quickly like that, be it to just assert something or to trial `clearly` before committing, you still can. Just start the server in-process:
> >
> > ```python
> >     from clearly.server import ClearlyServer
> >     clearly_server = ClearlyServer('<broker_url>', '<backend>')
> >     clearly_server.start_server(<port>)
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
> clearlycli = ClearlyClient('<clearly_server>', <12223>)
> ```
> 
> That's it, you're good to go!
>
> <details>
> <summary>Constrained to Python 2.7?</summary>
>
> > Use the docker way! :)
> > <br>If you still really want this, maybe to embed in your legacy projects' shell, please use version 0.4.2 as in:
> > ```bash
> > $ pip install clearly==0.4.2
> > ```
> > 
> > This version is prior to the server split, so it connects directly to the broker, but should still work.
> > 
> > You could also use 0.6.4, which is newer and already has a server, but please do mind that gRPC and Python 2.7 have a very annoying bug in this case: you can't CTRL+C out of `clearly` client's `capture` method (or any streaming methods), so you have to kill the process itself when needed with CTRL+\\. For more details on this nasty bug:
> > - https://github.com/grpc/grpc/issues/3820
> > - https://github.com/grpc/grpc/issues/6999
> > - https://bugs.python.org/issue8844
> </details>
</details>

---

## How to use it

So, you are ready to see tasks popping up in your screen faster than you can see? (Remember to filter them!)


### Grab them

#### In real time ⚡️
```python
clearlycli.capture()
clearlycli.capture_tasks()
clearlycli.capture_workers()
```

#### Past, stored events 🗄
```python
clearlycli.tasks()
clearlycli.workers()
```

Example using the `capture()` method, which will show all real time activity in the celery cluster, including both tasks and workers.

![capture](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_capture.png)

The real time method variants block to receive streaming events from the server.
<br>At any moment, you can CTRL+C out them, and rest assured the server will continue to gather all events seamlessly, it's just this client that will stop _receiving_ them. The `capture_tasks()` and `capture_workers()` methods receive only its respective real time events.
<br>The `tasks()` and `workers()` methods operates similarly, but retrieving only stored events without blocking.

The client will display those events in a format configured by the corresponding Display Mode.


### Display modes

```python
clearlycli.display_modes()
```

Display modes specify the level of details you want to see. Things like to show or not arguments being sent, to show exceptions, with or without arguments, to show tasks' results, etc.

![display modes](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_display_modes.png)

To change a display mode, just call the same method with the constant number beside it or the enum constant.

```python
clearlycli.display_modes(ModeTask.RESULT, ModeWorker.STATS)  # the enums are automatically imported
clearlycli.display_modes(2, 13)  # has the same effect, but easier on the fingers
```

You can also change only one display mode at a time (just call with one argument).

```python
clearlycli.display_modes(ModeTask.SUCCESS)  # the same as calling with (5)
clearlycli.display_modes(12)  # sets the worker display mode to ModeWorker.WORKER
```

And even configure the default directly in the `docker run` env: just include a `-e CLI_DISPLAY_MODES="..."`, with one or two _constant numbers_ (the enum constants are not accepted here).


### Seen tasks, metrics and reset tasks

```python
clearlycli.seen_tasks()  # prints all seen task types
clearlycli.metrics()  # prints some metrics about the celery cluster and Clearly itself
clearlycli.reset_tasks()  # resets stored tasks
```

This section should be pretty self-explanatory.

![seen metrics](https://raw.githubusercontent.com/rsalmei/clearly/master/img/clearly_seen_metrics.png)

---

## How `clearly` works

`Clearly` has started as a fully contained tool, one that you just run in a python REPL and filter tasks! It used to connect directly to the broker, which had several shortcomings like stressing the broker a lot (repeating **all events** to all connected `clearly`s), and losing all history whenever it was closed.

Nowadays, its software architecture is quite different. Since version 0.5, it is split in two software components: a server that extracts events and share data, and a client that interfaces with it, sending commands and displaying results.

`Clearly` **server** has three subsystems: the listener, the dispatcher and the RPC server. The listener runs on a background thread, that captures raw celery events in real time directly from the broker, updates their tasks in an LRU cache and dynamically generates missing states if needed (so it seems the events were perfectly ordered to the user). The dispatcher runs two other threads that handle connected users, filtering and dispatching selected events to the interested parties. The RPC server implements the gRPC communication mechanism.

The events in the _server_ may (and usually will) come in a chaotic order, so it must dynamically generate missing states and ignore late ones, so you never see a STARTED task before it being even RECEIVED, which would be weird. In a real time monitoring system this is very important, as it's not only about displaying the current state, but displaying the complete train of events that lead up to that state.

`Clearly` **client** can filter real time and persisted tasks by name, uuid, routing key and state, and workers by hostname, including brief metrics about the `clearly` _server_ itself. It has advanced formatting and syntax highlighting abilities, and configurable display modes to exhibit selected data. It does not use any threads and is totally broker and celery agnostic, relying only on the server via gRPC.

The arguments of the tasks are safely compiled into an AST (_Abstract Syntax Tree_), and beautifully syntax highlighted. Successful tasks get their results directly from the result backend if available, to overcome the problem of truncated results (the broker events have a size limit).

All async workers' life cycles are also processed and displayed, beautifully syntax highlighted too.
If you enable `task_send_sent_event`, all triggered tasks show up immediately on screen (it's quite nice to see!).

The memory consumption for server persisted tasks, although very optimized, must of course be limited. By default it stores 10,000 tasks and 100 workers at a time, and is configurable.

---

## Client commands Reference

```python
def capture_tasks(self, tasks: Optional[str] = None,
                  mode: Union[None, int, ModeTask] = None) -> None:
    """Start capturing task events in real time, so you can instantly see exactly
    what your publishers and workers are doing. Filter as much as you can to find
    what you need, and don't worry as the Clearly Server will still seamlessly
    handle all tasks updates.

    Currently, you can filter tasks by name, uuid, routing key or state.
    Insert an '!' in the first position to select those that do not match criteria.

    This runs in the foreground. Press CTRL+C at any time to stop it.

    Args:
        tasks: a simple pattern to filter tasks
            ex.: 'email' to find values containing that word anywhere
                 'failure|rejected|revoked' to find tasks with problem
                 '^trigger|^email' to find values starting with any of those words
                 'trigger.*123456' to find values with those words in that sequence
                 '!^trigger|^email' to filter values not starting with both those words
        mode: an optional display mode to present data

    See Also:
        ClearlyClient#display_modes()

    """

def capture_workers(self, workers: Optional[str] = None,
                    mode: Union[None, int, ModeWorker] = None) -> None:
    """Start capturing worker events in real time, so you can instantly see exactly
    what your workers states are. Filter as much as you can to find
    what you need, and don't worry as the Clearly Server will still seamlessly
    handle all tasks and workers updates.

    Currently, you can filter workers by hostname.
    Insert an '!' in the first position to select those that do not match criteria.

    This runs in the foreground. Press CTRL+C at any time to stop it.

    Args:
        workers: a simple pattern to filter workers
            ex.: 'email' to find values containing that word anywhere
                 'service|priority' to find values containing any of those words
                 '!service|priority' to find values not containing both those words
        mode: an optional display mode to present data

    See Also:
        ClearlyClient#display_modes()

    """

def capture(self, tasks: Optional[str] = None, workers: Optional[str] = None,
            modes: Union[None, int, ModeTask, ModeWorker, Tuple] = None) -> None:
    """Start capturing all events in real time, so you can instantly see exactly
    what your publishers and workers are doing. Filter as much as you can to find
    what you need, and don't worry as the Clearly Server will still seamlessly
    handle all tasks and workers updates.

    This runs in the foreground. Press CTRL+C at any time to stop it.

    Args:
        tasks: the pattern to filter tasks
        workers: the pattern to filter workers
        modes: optional display modes to present data
            send one or a tuple, as described in display_modes()

    See Also:
        ClearlyClient#capture_tasks()
        ClearlyClient#capture_workers()
        ClearlyClient#display_modes()

    """

def tasks(self, tasks: Optional[str] = None, mode: Union[None, int, ModeTask] = None,
          limit: Optional[int] = None, reverse: bool = True) -> None:
    """Fetch current data from past tasks.

    Note that the `limit` field is just a hint, it may not be accurate.
    Also, the total number of tasks fetched may be slightly different from
    the server `max_tasks` setting.

    Args:
        tasks: the pattern to filter tasks
        mode: an optional display mode to present data
        limit: the maximum number of events to fetch, fetches all if None or 0 (default)
        reverse: if True (default), shows the most recent first

    See Also:
        ClearlyClient#capture_tasks()
        ClearlyClient#display_modes()

    """

def workers(self, workers: Optional[str] = None,
            mode: Union[None, int, ModeWorker] = None) -> None:
    """Fetch current data from known workers.
    
    Args:
        workers: the pattern to filter workers
        mode: an optional display mode to present data

    See Also:
        ClearlyClient#capture_workers()
        ClearlyClient#display_modes()

    """

def seen_tasks(self) -> None:
    """Fetch a list of seen task types."""

def reset_tasks(self) -> None:
    """Reset stored tasks."""

def metrics(self) -> None:
    """List some metrics about the celery cluster and Clearly itself.

    Shows:
        Tasks processed: actual number of tasks processed, including retries
        Events processed: total number of events processed
        Tasks stored: number of currently stored tasks
        Workers stored: number of workers seen, including offline

    """
```

---

## Hints to extract the most out of it

- write a small [celery router](http://docs.celeryproject.org/en/latest/userguide/routing.html#routers) and generate dynamic routing keys, based on the actual arguments of the async call in place. That way, you'll be able to filter tasks based on any of those, like an id of an entity or the name of a product! Remember the args and kwargs are not used in the filtering.
- if you're using [django](https://www.djangoproject.com/) and [django-extensions](https://github.com/django-extensions/django-extensions), put in your settings a `SHELL_PLUS_POST_IMPORT` to auto import `clearly`! Just create a module to initialize a `clearlycli` instance for the django `shell_plus` and you're good to go. It's really nice to have `Clearly` always ready to be used, without importing or configuring anything, and quickly see what's going on with your tasks, even in production :)
- the more you filter, the less you'll have to analyze and debug! A production environment can have an overwhelmingly high number of tasks, like thousands of tasks per minute, so filter wisely.

---

## Maybe some day

- ~~support python 3;~~
- ~~split `Clearly` client and server, to allow an always-on server to run, with multiple clients connecting, without any of the shortcomings;~~
- ~~remove python 2 support~~
- ~~dockerize the server, to make its deploy way easier;~~
- improve the client command line, to be able to call `capture()` and others right from the shell;
- make the search pattern apply to args and kwargs too;
- support to constrain search pattern to only some fields;
- ability to hide sensitive information, directly in event listener;
- secure connection between server and client;
- any other ideas welcome!

---

## Changelog:
- 0.9.2: fix a warning on client startup
- 0.9.1: fix `reset()` breaking protobuf serialization; also rename it to `reset_tasks()`
- 0.9.0: major code revamp with new internal flow of data, in preparation to the 1.0 milestone! Now there's two StreamingDispatcher instances, each with its own thread, to handle tasks and workers separately (reducing ifs, complexity and latency); include type annotation in all code; several clearlycli improvements: introduced the "!" instead of "negate", introduced display modes instead of "params, success and error", renamed `stats()` to `metrics()`, removed `task()` and improved `tasks()` to also retrieve tasks by uuid, general polish in all commands and error handling; server log filters passwords from both broker and result backend; worker states reengineered, and heartbeats now get through to the client; unified the streaming and stored events filtering; refactor some code with high cyclomatic complexity; include the so important version number in both server and client initializations; adds a new stylish logo; friendlier errors in general; fix a connection leak, where streaming clients were not being disconnected; included an env var to configure default display modes; streamlined the test system, going from ~2600 tests down to less than 700, while keeping the same 100% branch coverage (removed fixtures combinations which didn't make sense); requires Python 3.6+
- 0.8.3: extended user friendliness of gRPC errors to all client rpc methods; last version to support Python 3.5
- 0.8.2: reduce docker image size; user friendlier gRPC errors on client capture (with --debug to raise actual exception); nicer client autocomplete (no clearly package or clearly dir are shown)
- 0.8.1: keep un-truncate engine from breaking when very distant celery versions are used in publisher and server sides
- 0.8.0: clearly is dockerized! both server and client are now available in rsalmei/clearly docker hub; include new `capture_tasks` and `capture_workers` methods; fix task result being displayed in RETRY state; detect and break if can't connect to the broker
- 0.7.0: code cleanup, supporting only Python 3.5+
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

---

## License
This software is licensed under the MIT License. See the LICENSE file in the top distribution directory for the full license text.

---

## Did you like it?

Thank you for your interest!

I've put much ❤️ and effort into this.

I wish you have fun using `Clearly`! :)
