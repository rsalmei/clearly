import functools
from collections import namedtuple
from datetime import datetime
from typing import Any, Callable, Iterable, Optional, Tuple, Union

import grpc
from about_time import about_time
from about_time.core import HandleStats
# noinspection PyProtectedMember
from celery.states import FAILURE, PROPAGATE_STATES, REJECTED, RETRY, REVOKED, SUCCESS

from .code_highlighter import traceback_highlighter_factory, typed_code
from .display_modes import ModeTask, ModeWorker, find_mode
from ..protos.clearly_pb2 import CaptureRequest, FilterTasksRequest, FilterWorkersRequest, Null, \
    PatternFilter, TaskMessage, WorkerMessage
from ..protos.clearly_pb2_grpc import ClearlyServerStub
from ..utils.colors import Colors
from ..utils.env_params import get_env_int_tuple
from ..utils.safe_compiler import safe_compile_text
from ..utils.worker_states import HEARTBEAT, ONLINE

HEADER_SIZE = 8
HEADER_PADDING, HEADER_ALIGN = ' ' * HEADER_SIZE, '>{}'.format(HEADER_SIZE)
EMPTY = Colors.DIM(':)')
DIM_NONE = Colors.CYAN_DIM('None')
TRACEBACK_HIGHLIGHTER = traceback_highlighter_factory()

Modes = namedtuple('Modes', 'tasks workers')


def set_user_friendly_errors(fn: Callable[..., None]) -> Callable[..., None]:
    @functools.wraps(fn)
    def inner(self: 'ClearlyClient', *args, **kwargs):
        try:
            fn(self, *args, **kwargs)
        except grpc.RpcError as e:
            if self._debug:
                raise
            # noinspection PyUnresolvedReferences
            print('{}: {} ({})'.format(
                Colors.BOLD('Server communication error'),
                Colors.RED(e.details()),
                Colors.DIM(e.code())
            ))
        except UserWarning as e:
            print(Colors.RED(e))

    return inner


class ClearlyClient:
    """Main client object, which interfaces with the Clearly server backend, sends
    commands and displays captured events.

    Attributes:
        _debug: if True, let the ugly  errors be seen, humanizes them otherwise
        _stub: the rpc communication stub instance
        _modes: the current tasks and workers display modes

    """

    def __init__(self, host: str = 'localhost', port: int = 12223, debug: bool = False):
        """Construct a Clearly Client instance.
        
        Args:
            host: the hostname of the server
            port: the port of the server

        """
        self._debug = debug
        channel = grpc.insecure_channel('{}:{}'.format(host, port))
        self._stub = ClearlyServerStub(channel)
        self._modes = Modes(ModeTask.FAILURE, ModeWorker.WORKER)
        self._modes = self._get_display_modes(get_env_int_tuple('CLI_DISPLAY_MODES', None))

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
        self.capture(tasks=tasks, modes=mode, workers='!')

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
        self.capture(workers=workers, modes=mode, tasks='!')

    @set_user_friendly_errors
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

        tasks_filter = ClearlyClient._parse_pattern(tasks)
        workers_filter = ClearlyClient._parse_pattern(workers)
        if not tasks_filter and not workers_filter:
            raise UserWarning('Nothing would be selected.')

        mode = self._get_display_modes(modes)
        request = CaptureRequest(
            tasks_capture=tasks_filter, workers_capture=workers_filter,
        )
        try:
            for realtime in self._stub.capture_realtime(request):
                if realtime.HasField('task'):
                    self._display_task(realtime.task, mode.tasks)
                elif realtime.HasField('worker'):
                    self._display_worker(realtime.worker, mode.workers)
                else:
                    print('unknown event:', realtime)
                    break
        except KeyboardInterrupt:  # pragma: no cover
            pass

    @set_user_friendly_errors
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
        tasks_filter = ClearlyClient._parse_pattern(tasks)
        if not tasks_filter:
            raise UserWarning('Nothing would be selected.')

        mode = self._get_display_modes(mode)
        request = FilterTasksRequest(
            tasks_filter=tasks_filter, limit=limit, reverse=reverse
        )

        at = about_time(self._stub.filter_tasks(request))
        for task in at:
            self._display_task(task, mode.tasks)
        ClearlyClient._fetched_info(at)

    @set_user_friendly_errors
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
        workers_filter = ClearlyClient._parse_pattern(workers)
        if not workers_filter:
            raise UserWarning('Nothing would be selected.')

        mode = self._get_display_modes(mode)
        request = FilterWorkersRequest(workers_filter=workers_filter)

        at = about_time(self._stub.filter_workers(request))
        for worker in at:
            self._display_worker(worker, mode.workers)
        ClearlyClient._fetched_info(at)

    @set_user_friendly_errors
    def seen_tasks(self) -> None:
        """Fetch a list of seen task types."""
        task_types = self._stub.seen_tasks(Null()).task_types
        for i, task_type in enumerate(task_types, 1):
            print(Colors.DIM(i), Colors.BLUE(task_type))

    @set_user_friendly_errors
    def reset_tasks(self) -> None:
        """Reset stored tasks."""
        self._stub.reset_tasks(Null())
        print(Colors.BLUE('Ok'))

    @set_user_friendly_errors
    def metrics(self) -> None:
        """List some metrics about the celery cluster and Clearly itself.

        Shows:
            Tasks processed: actual number of tasks processed, including retries
            Events processed: total number of events processed
            Tasks stored: number of currently stored tasks
            Workers stored: number of workers seen, including offline

        """
        stats = self._stub.get_metrics(Null())
        print(Colors.DIM('Processed:'),
              '\ttasks', Colors.RED(stats.task_count),
              '\tevents', Colors.RED(stats.event_count))
        print(Colors.DIM('Stored:'),
              '\ttasks', Colors.RED(stats.len_tasks),
              '\tworkers', Colors.RED(stats.len_workers))

    def _get_display_modes(self, modes: Union[None, int, ModeTask, ModeWorker, Tuple] = None) \
            -> Modes:
        if not isinstance(modes, tuple):
            modes = (modes,)
        elif len(modes) > 2:
            raise UserWarning('At most two display modes, was sent {}'
                              .format(len(modes)))

        modes = sorted(x for x in (find_mode(to) for to in modes) if x)
        if not modes:
            return self._modes
        if len(modes) == 2 and isinstance(modes[0], type(modes[1])):
            raise UserWarning('Two modes of the same type?')

        if isinstance(modes[0], ModeTask):
            return Modes(modes[0], modes[1] if len(modes) == 2 else self._modes.workers)
        return Modes(self._modes.tasks, modes[0])

    @set_user_friendly_errors
    def display_modes(self, *modes: Union[None, int, ModeTask, ModeWorker, Tuple]) -> None:
        """Show available display modes, including the currently selected ones, or
        change the current task/worker modes, sending one or two arguments of any type.
        See that constant number beside modes? You can rapidly set modes with them!

        Args:
            modes: a display mode to set, either task or worker, or its constant number
                send two to set both display modes in one call

        """
        if modes:
            self._modes = self._get_display_modes(modes)

        modes = ('tasks', ModeTask, self._modes.tasks), ('workers', ModeWorker, self._modes.workers)
        for title, klass, var_mode in modes:
            print(Colors.BLUE(title))
            for d in klass:
                print('  {} {:8} {}: {}'.format(
                    d == var_mode and '*' or ' ', d.name,
                    Colors.ORANGE_BOLD(d.value, '>2'), Colors.YELLOW(d.description)))

    @staticmethod
    def _fetched_info(at: HandleStats) -> None:  # pragma: no cover
        print('{} {} in {} ({})'.format(
            Colors.DIM('fetched:'), Colors.BOLD(at.count),
            Colors.GREEN(at.duration_human), Colors.GREEN(at.throughput_human)
        ))

    @staticmethod
    def _parse_pattern(pattern: str) -> PatternFilter:
        if not isinstance(pattern, (type(None), str)):
            raise UserWarning('Invalid pattern.')

        pattern = (pattern or '').strip()
        negate = pattern.startswith('!')
        pattern = pattern[negate:].strip() or '.'
        if negate and pattern == '.':
            return
        return PatternFilter(pattern=pattern, negate=negate)

    @staticmethod
    def _display_task(task: TaskMessage, mode: ModeTask) -> None:
        params, success, error = mode.spec
        ts = datetime.fromtimestamp(task.timestamp)
        print(Colors.DIM(ts.strftime('%H:%M:%S.%f')[:-3]), end=' ')
        if not task.state:
            routing_key = task.routing_key or EMPTY
            print(Colors.BLUE(task.name),
                  Colors.MAGENTA(routing_key[len(task.name):] or '-'
                                 if routing_key.startswith(task.name)
                                 else routing_key),
                  Colors.DIM(task.uuid))
        else:
            print(ClearlyClient._task_state(task.state),
                  Colors.BLUE_DIM(task.retries),
                  end=' ')
            print(Colors.BLUE(task.name), Colors.DIM(task.uuid))

        show_outcome = (task.state in PROPAGATE_STATES and error) \
            or (task.state == SUCCESS and success)

        first_seen = bool(params) and not task.state
        params_outcome = params is not False and show_outcome
        if first_seen or params_outcome:
            print(Colors.DIM('args:', HEADER_ALIGN),
                  typed_code(safe_compile_text(task.args), wrap=False) or EMPTY)
            print(Colors.DIM('kwargs:', HEADER_ALIGN),
                  typed_code(safe_compile_text(task.kwargs), wrap=False) or EMPTY)

        if show_outcome:
            if task.state == SUCCESS:
                result = safe_compile_text(task.result)
                outcome = ' '.join((Colors.CYAN_DIM('<{}>'.format(task.result_meta)),
                                    EMPTY if result is None else typed_code(result)))
            else:
                outcome = TRACEBACK_HIGHLIGHTER(task.traceback) \
                    .replace('\n', '\n' + HEADER_PADDING).strip()
            print(Colors.DIM('==>', HEADER_ALIGN), outcome)

    @staticmethod
    def _display_worker(worker: WorkerMessage, mode: ModeWorker) -> None:
        stats, = mode.spec
        if worker.timestamp:
            ts = datetime.fromtimestamp(worker.timestamp)
            print(Colors.DIM(ts.strftime('%H:%M:%S.%f')[:-3]), end=' ')
        print(ClearlyClient._worker_state(worker.state),
              Colors.CYAN_DIM(worker.hostname),
              Colors.YELLOW_DIM(str(worker.pid)))

        if stats:
            print(Colors.DIM('sw:', HEADER_ALIGN),
                  Colors.CYAN_DIM(' '.join((worker.sw_sys, worker.sw_ident))),
                  Colors.ORANGE(worker.sw_ver))
            print(Colors.DIM('load:', HEADER_ALIGN),
                  ClearlyClient._item_list(worker.loadavg),
                  Colors.DIM('processed:'), worker.processed or DIM_NONE)
            heartbeats = [datetime.fromtimestamp(x).strftime('%H:%M:%S.%f')[:-3]
                          for x in worker.heartbeats or []]
            print(Colors.DIM('heartb:', HEADER_ALIGN),
                  '{}{}'.format(Colors.ORANGE(worker.freq),
                                Colors.DIM('s')),
                  ClearlyClient._item_list(heartbeats))

    @staticmethod
    def _item_list(items: Iterable[Any], color: Callable[[str], str] = str) -> str:
        return '{}{}{}'.format(
            Colors.MAGENTA('['),
            Colors.MAGENTA(', ').join(map(color, items)),
            Colors.MAGENTA(']'),
        )

    @staticmethod
    def _task_state(state: str) -> None:
        if state == SUCCESS:  # final state in BOLD
            return Colors.GREEN_BOLD(state, HEADER_ALIGN)
        if state in (FAILURE, REVOKED, REJECTED):  # final too
            return Colors.RED_BOLD(state, HEADER_ALIGN)
        if state == RETRY:  # transient state with a failure.
            return Colors.ORANGE(state, HEADER_ALIGN)
        return Colors.YELLOW(state, HEADER_ALIGN)  # transient states

    @staticmethod
    def _worker_state(state: str) -> None:
        result = state
        if state == HEARTBEAT:
            return Colors.GREEN(result)
        if state == ONLINE:
            return Colors.GREEN_BOLD(result)
        return Colors.RED_BOLD(result)
