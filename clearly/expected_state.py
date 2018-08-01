# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import six
from celery import states

from .utils import worker_states


class ExpectedStateHandler(object):
    """Events received can be totally out of order, which is not a problem for
    the final state, as celery itself takes into account their precedence.
    Flower doesn't care either, as it shows a snapshot at that moment.
    
    But for Clearly, which shows in real-time what is happening with the tasks,
    it was very odd to show one with a RETRY state, before it was even STARTED,
    or STARTED before being RECEIVED.
    This class fixes that, with a state machine of the expected states, which 
    dynamically generates the missing states.
    
    """

    def __init__(self, expected_path):
        self.expected_path = expected_path  # type:ExpectedPath

    def states_through(self, pre, post):
        if pre == post:
            raise StopIteration

        pointer = self.expected_path
        expected = pre
        seen = [pointer.name]
        while pointer.name != expected:
            pointer = pointer.find(expected)
            if pointer.name in seen:
                raise ValueError('impossible to start from {}'.format(pre))
            seen.append(pointer.name)

        expected = post
        seen = [pointer.name]
        while True:
            pointer = pointer.find(expected)
            if pointer.name in seen:
                raise ValueError('impossible to go from {} to {}'.format(pre, post))
            seen.append(pointer.name)
            yield pointer.name
            if pointer.name == expected:
                break


class ExpectedPath(object):
    def __init__(self, name):
        assert isinstance(name, six.string_types)
        self.name = name
        self.possibles = ()
        self.default = None

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
    expected_path = ExpectedPath(states.PENDING)
    return_path = expected_path.to(states.RECEIVED)
    # noinspection PyTypeChecker
    return_path.to(states.STARTED) \
        .to((states.SUCCESS,
             states.FAILURE,
             states.REJECTED,
             states.REVOKED,),
            states.RETRY) \
        .to(return_path)

    return ExpectedStateHandler(expected_path)


def setup_worker_states():
    expected_path = ExpectedPath(worker_states.OFFLINE)
    # noinspection PyTypeChecker
    expected_path.to(worker_states.ONLINE).to(expected_path)

    return ExpectedStateHandler(expected_path)
