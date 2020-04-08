from typing import Generator, Iterable, Tuple, Union

# noinspection PyProtectedMember
from celery.states import FAILURE, PENDING, RECEIVED, REJECTED, RETRY, REVOKED, STARTED, SUCCESS


class ExpectedPath:
    def __init__(self, name: str):
        self.name = name
        self.possibles = ()
        self.default = None

    def __repr__(self):  # pragma: no cover
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def to(self, names: Union[str, 'ExpectedPath', Tuple[Union[str, 'ExpectedPath'], ...]],
           default: Union[None, str, 'ExpectedPath'] = None) -> 'ExpectedPath':
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
        if self.default:
            return self.default
        if len(self.possibles) == 1:
            return self.possibles[0]
        raise UserWarning('unknown name {} in {}'.format(name, self.name))


class ExpectedStateHandler:
    """Events received will usually be totally disordered, which is not a
    problem for the final state, as celery itself takes into account their
    precedence. Flower doesn't care either, as it uses that same final state.
    
    But for Clearly, which shows tasks in real time, it was very odd to show
    RETRY states before STARTED, or SUCCESS before they were even RECEIVED!
    This class fixes that, with a state machine of the expected states, which 
    dynamically generates the missing states.

    """

    def __init__(self, expected_path: ExpectedPath):
        self.expected_path: ExpectedPath = expected_path

    @staticmethod
    def __traverse(pre: ExpectedPath, target: str, yielding: bool) \
            -> Generator[str, None, ExpectedPath]:
        pointer, seen = pre, [pre.name]
        while pointer.name != target:
            pointer = pointer.find(target)
            if pointer.name in seen:
                raise ValueError('impossible to go from {} to {}'.format(pre.name, target))
            seen.append(pointer.name)
            if yielding:
                yield pointer.name
        return pointer

    def states_through(self, pre: str, post: str) -> Iterable[str]:
        if pre == post:
            return

        pointer = yield from self.__traverse(self.expected_path, pre, False)
        yield from self.__traverse(pointer, post, True)


def setup_task_states() -> ExpectedStateHandler:
    terminal = (SUCCESS, FAILURE, REJECTED, REVOKED)

    pending = ExpectedPath(PENDING)
    received = pending.to(RECEIVED)
    received.to(STARTED) \
        .to(terminal, RETRY) \
        .to(pending, received)

    return ExpectedStateHandler(pending)
