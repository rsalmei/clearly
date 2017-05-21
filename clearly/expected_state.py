# coding=utf-8
from __future__ import unicode_literals

from contextlib import contextmanager

from celery import states


class ExpectedStateHandler(object):
    """Events received can be totally out of order, which is not a problem for
    the final state, as celery itself takes into account their precedence.
    Flower doesn't care either, as it shows a snapshot at that moment.
    
    But for Clearly, which shows in real-time was is happening with the tasks,
    it was very odd to show one with a RETRY state, before it was even STARTED,
    or STARTED before being RECEIVED.
    This class fixes that, with a state machine of the expected states, which 
    dynamically generates the missing states.
    
    """
    pre = post = None

    def __init__(self, field, expected_path):
        self.field = field
        self.expected_path = expected_path  # type:ExpectedPath

    @contextmanager
    def track_changes(self, obj):
        self.pre = getattr(obj, self.field)
        yield
        self.post = getattr(obj, self.field)

    def states_through(self):
        if self.pre == self.post or (self.post == self.expected_path.name
                                     and self.expected_path.ignore):
            raise StopIteration

        pointer = self.expected_path
        expected = self.pre
        while pointer.name != expected:
            pointer = pointer.find(expected)

        expected = self.post
        stop = pointer.name
        while True:
            pointer = pointer.find(expected)
            yield pointer.name
            if pointer.name in (expected, stop):
                break


class ExpectedPath(object):
    def __init__(self, name, ignore=False):
        self.name = name
        self.possibles = None
        self.default = None
        self.ignore = ignore

    def to(self, names, default=None):
        if not isinstance(names, tuple):
            names = (names,)
        paths = tuple(ExpectedPath(name) if
                      not isinstance(name, ExpectedPath) else name
                      for name in names)
        self.possibles = (self.possibles or ()) + paths
        if default:
            self.default = ExpectedPath(default) if \
                not isinstance(default, ExpectedPath) else default
        return paths[0] if len(names) == 1 else self.default

    def find(self, name):
        for n in self.possibles:
            if n.name == name:
                return n
        if len(self.possibles) == 1:
            return self.possibles[0]
        if self.default:
            return self.default
        raise UserWarning('unknown name {} in {}'.format(name, self.name))


def setup_task_states():
    expected_path = ExpectedPath(states.PENDING, True)
    return_path = expected_path.to(states.RECEIVED)
    # noinspection PyTypeChecker
    return_path.to(states.STARTED) \
        .to((states.SUCCESS,
             states.FAILURE,
             states.REJECTED,
             states.REVOKED,),
            states.RETRY) \
        .to(return_path)

    return ExpectedStateHandler('state', expected_path)


def setup_worker_states():
    expected_path = ExpectedPath(False, False)
    # noinspection PyTypeChecker
    expected_path.to(True).to(expected_path)

    return ExpectedStateHandler('alive', expected_path)
