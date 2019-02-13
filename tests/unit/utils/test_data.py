import re

import pytest

from clearly.protos.clearly_pb2 import TaskMessage, WorkerMessage
from clearly.utils.data import accepts, copy_update


@pytest.fixture(params=(True, False))
def negate(request):
    yield request.param


@pytest.mark.parametrize('regex, values, expected', [
    (r'.', ('a',), True),
    (r'.', ('agagfsa', ''), True),
    (r'.', ('', 'ggfdagfds'), True),
    (r'.', ('',), False),
    (r'.', ('', '', ''), False),
    (r'a', ('a',), True),
    (r'a', ('b',), False),
    (r'a', ('', 'zxc', 'qwe', 'bab'), True),
    (r'a', ('bbbbbb', ''), False),
    (r'a', ('', 'bbbabbb', ''), True),
    (r'a', ('',), False),
    (r'ab|ac', ('bbbbaaaa',), False),
    (r'ab|ac', ('bbbbaaaab',), True),
    (r'ab|ac', ('', 'a'), False),
    (r'ab|ac', ('', 'aaaaaa'), False),
    (r'ab|ac', ('aabb', ''), True),
    (r'ab|ac', ('aabb', 'aacc'), True),
    (r'ab|ac', ('aaaa', 'aacc'), True),
    (r'ab|ac', ('aaaa', 'bbbb'), False),
])
def test_data_client_accepts(regex, values, expected, negate):
    assert accepts(re.compile(regex), negate, *values) == (expected ^ negate)


@pytest.mark.parametrize('original, values', [
    (TaskMessage(), dict()),
    (TaskMessage(name='name'), dict()),
    (TaskMessage(), dict(uuid='uuid')),
    (TaskMessage(), dict(name='name', uuid='uuid')),
    (TaskMessage(), dict(name='name', uuid='uuid', timestamp=12345, created=False)),
    (TaskMessage(name='name', created=False), dict(uuid='uuid')),
    (TaskMessage(name='name', created=False), dict(uuid='uuid', timestamp=12345)),
    (TaskMessage(name='name'), dict(name='changed')),
    (TaskMessage(name='name', timestamp=12345), dict(name='changed', timestamp=23456)),
    (WorkerMessage(), dict()),
    (WorkerMessage(hostname='host'), dict()),
    (WorkerMessage(), dict(hostname='host')),
    (WorkerMessage(last_heartbeat=123), dict(hostname='host')),
    # (RealtimeEventMessage(), dict()),
    # (RealtimeEventMessage(task=TaskMessage()), dict()),
    # (RealtimeEventMessage(), dict(task=TaskMessage())),
])
def test_data_copy_update(original, values):
    copy = copy_update(original, **values)
    assert type(original) == type(copy)
    assert original is not copy
    for f in original.DESCRIPTOR.fields_by_name.keys():
        assert getattr(copy, f) == values.pop(f, getattr(original, f))
    for f in values:
        assert getattr(copy, f) == getattr(original, f)

    # support for submessage fields someday.
    # if not f.message_type:
    # if original.HasField(f) or f in values:
    #     assert copy.HasField(f)
    #     assert getattr(copy, f) == expected
    # else:
    #     assert not copy.HasField(f)
