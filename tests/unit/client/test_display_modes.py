import pytest

from clearly.client.display_modes import find_mode
from clearly.client import ModeTask, ModeWorker


@pytest.mark.parametrize('constant', [
    '', 'ALL', 1.1, object(), -1, 1 + len(ModeTask.__members__) + len(ModeWorker.__members__)
])
def test_find_mode_error(constant):
    with pytest.raises(UserWarning):
        # noinspection PyTypeChecker
        assert find_mode(constant)


@pytest.mark.parametrize('constant, expected', [
    (None, None),
    *((c, c) for c in ModeTask.__members__.values()),
    *((c, c) for c in ModeWorker.__members__.values()),
    *((c.value, c) for c in ModeTask.__members__.values()),
    *((c.value, c) for c in ModeWorker.__members__.values()),
])
def test_find_mode(constant, expected):
    assert find_mode(constant) == expected
