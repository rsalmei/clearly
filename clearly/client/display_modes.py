from enum import Enum
from typing import Union

_VALUES = {}


class EnumSpecDescription(Enum):
    def __new__(cls, description, *spec):
        obj = object.__new__(cls)
        obj._value_ = len(_VALUES) + 1
        _VALUES[obj._value_] = obj
        obj.__description = description
        obj.__spec = spec
        return obj

    def __repr__(self):  # pragma: no cover
        return '<{}.{}: {} {!r}>'.format(self.__class__.__name__, self.name,
                                         self.value, self.__description)

    def __lt__(self, other):  # pragma: no cover
        if issubclass(self.__class__, EnumSpecDescription):
            return self.value < other.value

    def __le__(self, other):  # pragma: no cover
        if issubclass(self.__class__, EnumSpecDescription):
            return self.value <= other.value

    def __gt__(self, other):  # pragma: no cover
        if issubclass(self.__class__, EnumSpecDescription):
            return self.value > other.value

    def __ge__(self, other):  # pragma: no cover
        if issubclass(self.__class__, EnumSpecDescription):
            return self.value >= other.value

    @property
    def spec(self):
        return self.__spec

    @property
    def description(self):
        return self.__description


class ModeTask(EnumSpecDescription):
    TASK = 'name, uuid, routing key, state and retries', False, False, False

    RESULT = 'TASK + results', False, True, False
    ERROR = 'TASK + exceptions', False, False, True
    OUTCOME = 'RESULT + ERROR', False, True, True

    SUCCESS = 'RESULT + args/kwargs', None, True, False
    FAILURE = 'ERROR + args/kwargs', None, False, True
    DONE = 'SUCCESS + FAILURE', None, True, True

    SENT = 'TASK + args/kwargs being sent', True, False, False
    FLOWING = 'SENT + SUCCESS', True, True, False
    BREAKING = 'SENT + FAILURE', True, False, True
    ALL = 'SENT + DONE', True, True, True


class ModeWorker(EnumSpecDescription):
    WORKER = 'name, status and pid', False
    STATS = 'WORKER + version, load and heartbeats', True


def find_mode(constant: Union[None, int, ModeTask, ModeWorker]) \
        -> Union[None, ModeTask, ModeWorker]:
    if isinstance(constant, (type(None), ModeTask, ModeWorker)):
        return constant
    if isinstance(constant, int) and constant in _VALUES:
        return _VALUES[constant]
    raise UserWarning('Invalid mode constant.')
