# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import socket
import time

import six
from celery import states
from collections import OrderedDict
from kombu import Exchange, Queue, binding

from clearly.task_info import TaskInfo
from clearly.utils.colors import colors

HEADER_SIZE = 8
SEPARATOR = colors.RED(', ')
KWARGS_SEPARATOR = colors.RED('=')
DICT_SEPARATOR = colors.RED(': ')
EMPTY = colors.DIM(':)')


class Clearly(object):
    """
        Simple and real-time monitor for celery.
    """

    def __init__(self, app, exchange):
        """Constructs a monitor instance.
        
        Args:
            app (celery.app): the configured celery app instance
            exchange (Union[str, Exchange]): the exchange instance or name 
                the celery publishes messages to

        """
        self._app = app
        if isinstance(exchange, Exchange):
            self._exchange = exchange
        else:
            self._exchange = Exchange(exchange, type='topic')

        # initialize variables
        self.reset()

    def capture(self, routing_keys,
                show_params=False, show_success=False, show_error=True):
        """Gathers all tasks being sent to celery that matches routing keys.
        You can press CTRL+C at any time to stop capturing, without losing
         anything already captured.
        
        Args:
            routing_keys (str): a string to be split into routing keys.
                use * as exactly one part or # as zero or more.
                ex.: 'dispatch.# email.#' to filter messages starting with
                      or 'dispatch.#.123456.#' to filter that exact id and pos
                      or even '#.123456.#' to filter that exact id anywhere.
            show_params (bool): if True shows params of all tasks
            show_success (bool): if True shows successful tasks' results
            show_error (bool): if True shows failed tasks' results
    
        """
        monitor_queue = Queue(exclusive=True,
                              durable=False,
                              bindings=[
                                  binding(exchange=self._exchange,
                                          routing_key=x)
                                  for x in routing_keys.split()])

        def process_message(body, message):
            task_id = body['id']

            # RETRY tasks pass again here.
            if task_id in self._waiting_tasks:
                async_result = self._waiting_tasks[task_id].async
            else:
                async_result = self._app.AsyncResult(task_id)

            # There's a race condition in task async results, which can be in
            # the process of update in the backend yet. Sometimes I would
            # receive a PENDING with a 1 retry count or a RETRY with a 0 retry
            # count... But the current retry count seems to be reliable.
            current_retry = body['retries']
            # Wow, even a SUCCESS has appeared here.
            current_state = states.RETRY if current_retry else states.PENDING

            task = TaskInfo(id=task_id, name=body['task'],
                            args=body['args'], kwargs=body['kwargs'],
                            async=async_result,
                            state=current_state,
                            retries=current_retry)

            if current_retry == 0:
                self._display_task(task, True, show_params, False)
            else:
                self._display_task(task, False, False, False)

            self._waiting_tasks[task_id] = task
            message.ack()

        with self._app.pool.acquire() as conn:
            with conn.Consumer(monitor_queue, callbacks=[process_message],
                               accept=['pickle']):
                while True:
                    try:
                        conn.drain_events(timeout=1)
                    except socket.timeout:
                        self._internal_fetch(show_success, show_error)
                    except KeyboardInterrupt:
                        break

    def _internal_fetch(self, show_success, show_error):
        for task in self._waiting_tasks.values():
            current_state = task.async.state
            if current_state not in (task.state, states.RETRY):
                if current_state in states.READY_STATES:
                    task = task._replace(state=current_state,
                                         result=task.async.result)
                    self._finished_tasks.append(task)
                    del self._waiting_tasks[task.id]
                else:
                    task = task._replace(state=current_state)
                    self._waiting_tasks[task.id] = task
                self._display_task(task, False, False,
                                   self._is_to_show_result(task.state,
                                                           show_success,
                                                           show_error))

    def fetch(self, show_success=False, show_error=True):
        """Fetches results of pending captured tasks, blocking if necessary.
    
        Args:
            show_success (bool): if True shows successful tasks' results
            show_error (bool): if True shows failed tasks' results
    
        """
        while self._waiting_tasks:
            try:
                self._internal_fetch(show_success, show_error)
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def pending(self, show_params=False):
        """Prints pending captured tasks.
    
        Args:
            show_params (bool): if True shows params of all tasks
    
        """
        for task in self._waiting_tasks.values():
            self._display_task(task, False, show_params, False)

    def results(self, show_success=False, show_error=True):
        """Prints captured tasks which have terminal status, specifically 
         success, failure or revoked status.
        
        Args:
            show_success (bool): if True shows successful tasks' results
            show_error (bool): if True shows failed tasks' results

        """
        for task in self._finished_tasks:
            show = self._is_to_show_result(task.state, show_success, show_error)
            self._display_task(task, False, show, show)

    def _is_to_show_result(self, state, show_success, show_error):
        return (state == states.FAILURE and show_error) \
               or (state == states.SUCCESS and show_success)

    def reset(self):
        """Resets all captured data.
        
        """
        self._waiting_tasks = OrderedDict()
        self._finished_tasks = []

    def _display_task(self, task, is_new, show_params, show_result):
        if not is_new:
            print(self._state_color(task.state, task.retries), end=' ')
        print(colors.BLUE(task.name), colors.DIM(task.id))

        if show_params:
            print(colors.DIM('{:>{}}'.format('args:', HEADER_SIZE)),
                  SEPARATOR.join(self._typed_text(x)
                                 for x in task.args) or EMPTY)
            print(colors.DIM('{:>{}}'.format('kwargs:', HEADER_SIZE)),
                  SEPARATOR.join('{}{}{}'.format(colors.ORANGE(k),
                                                 KWARGS_SEPARATOR,
                                                 self._typed_text(v))
                                 for k, v in task.kwargs.items()) or EMPTY)

        if show_result:
            print(colors.DIM('{:>{}}'.format('==>', HEADER_SIZE)),
                  self._typed_text(task.result))

    def _state_color(self, state, retries):
        result = '{:>{}} {}'.format(state, HEADER_SIZE, retries)
        if state == states.SUCCESS:  # final state in BOLD
            return colors.BOLD(colors.GREEN(result))
        if state in (states.FAILURE, states.REVOKED):  # final states in BOLD
            return colors.BOLD(colors.RED(result))
        return colors.YELLOW(result)  # transient state

    def _typed_text(self, p):
        if p is None:
            return colors.CYAN('None')
        if isinstance(p, (str, unicode)):
            return colors.YELLOW("'{}'".format(force_text(p)))
        if isinstance(p, (int, long, float)):
            return colors.MAGENTA(force_text(p))
        if isinstance(p, (list, tuple, set)):
            f = '[{}]' if isinstance(p, list) \
                else '({})' if isinstance(p, tuple) else '{{{}}}'
            return f.format(SEPARATOR.join(self._typed_text(x) for x in p))
        if isinstance(p, dict):
            return '{{{}}}'.format(
                SEPARATOR.join('{}{}{}'.format(self._typed_text(k),
                                               DICT_SEPARATOR,
                                               self._typed_text(v))
                               for k, v in p.items()))

        return force_text(repr(p))


def force_text(s, encoding='utf-8', errors='strict'):
    """Based on the django.text.encoding.force_text.
    
    """
    if isinstance(s, six.text_type):
        return s
    if not isinstance(s, six.string_types):
        if hasattr(s, '__unicode__'):
            s = s.__unicode__()
        else:
            s = six.text_type(bytes(s), encoding, errors)
    else:
        s = six.text_type(s, encoding, errors)
    return s
