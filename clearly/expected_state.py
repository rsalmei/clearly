from typing import Tuple, Iterable, Optional, Union

from celery import states as task_states

from .utils import worker_states


class ExpectedStateHandler:
    """Events received will usually be totally disordered, which is not a
    problem for the final state, as celery itself takes into account their
    precedence. Flower doesn't care either, as it uses that same final state.
    
    But for Clearly, which shows tasks in real time, it was very odd to show
    RETRY states before STARTED, or SUCCESS before they were even RECEIVED!
    This class fixes that, with a state machine of the expected states, which 
    dynamically generates the missing states.

    """

    def __init__(self, expected_path: 'ExpectedPath'):
        self.expected_path: ExpectedPath = expected_path

    @staticmethod
    def __traverse(pre, target, yielding):
        pointer, seen = pre, [pre.name]
        while pointer.name != target:
            pointer = pointer.find(target)
            if pointer.name in seen:
                raise ValueError('impossible to find from {}'.format(pre))
            seen.append(pointer.name)
            if yielding:
                yield pointer.name
        return pointer

    def states_through(self, pre: str, post: str) -> Iterable[str]:
        if pre == post:
            return

        pointer = yield from self.__traverse(self.expected_path, pre, False)
        yield from self.__traverse(pointer, post, True)


class ExpectedPath:
    def __init__(self, name: str):
        self.name = name
        self.possibles = ()
        self.default = None

    def to(self, names: Union[str, 'ExpectedPath', Tuple[Union[str, 'ExpectedPath'], ...]],
           default: Optional[str] = None) -> 'ExpectedPath':
        if not isinstance(names, tuple):
            names = (names,)
        paths = tuple(ExpectedPath(name) if isinstance(name, str) else name
                      for name in names)
        self.possibles = (self.possibles or ()) + paths
        if default:
            self.default = ExpectedPath(default) if isinstance(default, str) else default
        return paths[0] if len(names) == 1 else self.default

    def find(self, name: str) -> 'ExpectedPath':
        for n in self.possibles:
            if n.name == name:
                return n
        if len(self.possibles) == 1:
            return self.possibles[0]
        if self.default:
            return self.default
        raise UserWarning('unknown name {} in {}'.format(name, self.name))


def setup_task_states() -> ExpectedStateHandler:
    pending = ExpectedPath(task_states.PENDING)
    received = pending.to(task_states.RECEIVED)
    received \
        .to(task_states.STARTED) \
        .to((task_states.SUCCESS,
             task_states.FAILURE,
             task_states.REJECTED,
             task_states.REVOKED,), task_states.RETRY) \
        .to(received)


def setup_worker_states() -> ExpectedStateHandler:
    expected_path = ExpectedPath(worker_states.OFFLINE)
    expected_path.to(worker_states.ONLINE).to(expected_path)

    return ExpectedStateHandler(expected_path)
    return ExpectedStateHandler(pending)
