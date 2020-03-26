import operator
from typing import Pattern, Tuple, Union

from celery.events.state import Task, Worker

from ..protos.clearly_pb2 import TaskMessage, WorkerMessage

TASK_OP = operator.attrgetter('name', 'uuid', 'routing_key', 'state')
WORKER_OP = operator.attrgetter('hostname')


def obj_to_message(obj: Union[Task, Worker], to_type: Union[TaskMessage, WorkerMessage],
                   **updates) -> Union[TaskMessage, WorkerMessage]:
    """Convert celery Task/Worker objects to proto buffer messages, updating
    some fields as needed.

    Args:
        obj: the celery object to be converted
        to_type: desired message type
            Note: even having only one compatible type, the caller already has this info,
            and this avoids ifs here and so improve performance in this heavy usage method.

    Returns:
        key and proto buffer message

    """
    keys = to_type.DESCRIPTOR.fields_by_name.keys()
    data = {k: getattr(obj, k) for k in keys}
    data.update(updates)
    return to_type(**data)


def accept_task(pattern: Pattern, negate: bool, message: TaskMessage) -> bool:
    """Find if the message values match the given pattern and negate.
    This centralizes the search criteria, to both real time streaming
    and past events.

    """
    return _accept(pattern, negate, TASK_OP(message))


def accept_worker(pattern: Pattern, negate: bool, message: WorkerMessage) -> bool:
    """Find if the message values match the given pattern and negate.
    This centralizes the search criteria, to both real time streaming
    and past events.

    """
    return _accept(pattern, negate, WORKER_OP(message))


def _accept(pattern: Pattern, negate: bool, values: Tuple[str, ...]) -> bool:
    return any(v and pattern.search(v) for v in values) != negate
