import re
from typing import Callable

import pytest
from celery import states as task_states

from clearly.utils import worker_states
from clearly.client import ModeTask, ModeWorker


@pytest.fixture(params=sorted(task_states.ALL_STATES))
def task_state_type(request):
    yield request.param


@pytest.fixture(params=sorted(task_states.ALL_STATES.union({'?'})))
def task_state_plus_1(request):
    """Can be used for a double SUCCESS, which truncates results or not, or for a
    double PENDING, which is created or not."""
    # task results only make sense in success, so to test truncate resolving mechanism,
    # I can't just insert a bool, as almost all combinations would not make sense.
    # the same for pending.
    yield request.param


@pytest.fixture(params=sorted(task_states.ALL_STATES.union({'?1', '?2'})))
def task_state_plus_2(request):
    """Same as above, but with 2 additional states."""
    yield request.param


@pytest.fixture(params=sorted(worker_states.ALL_STATES))
def worker_state_type(request):
    yield request.param


@pytest.fixture(params=sorted(worker_states.TYPES.keys()))
def worker_event_type(request):
    yield request.param


@pytest.fixture(params=ModeTask.__members__.values())
def mode_task_type(request):
    yield request.param


@pytest.fixture(params=ModeWorker.__members__.values())
def mode_worker_type(request):
    yield request.param


@pytest.fixture(params=(True, False))
def bool1(request):
    yield request.param


@pytest.fixture(params=(True, False))
def bool2(request):
    yield request.param


@pytest.fixture(params=(True, False, None))
def tristate(request):
    yield request.param


@pytest.fixture
def strip_colors() -> Callable[[str], str]:
    def actual(text: str) -> str:
        return re.sub(r'\033\[.+?m', '', text)

    return actual
