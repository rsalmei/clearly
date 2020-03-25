def accepts(regex, negate, *values):
    """Given a compiled regex and a negate, find if any of the values match.
from typing import Pattern, Tuple, Union

from celery.events.state import Task, Worker

from ..protos.clearly_pb2 import TaskMessage, WorkerMessage
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


def copy_update(pb_message, **kwds):
    """Returns a copy of the PB object, with some fields updated.

    Args:
        pb_message:
        **kwds:

    Returns:

    """
    result = pb_message.__class__()
    result.CopyFrom(pb_message)
    for k, v in kwds.items():
        setattr(result, k, v)
    return result
