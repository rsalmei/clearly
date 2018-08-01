# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals


def accepts(regex, negate, *values):
    """Given a compiled regex and a negate, find if any of the values match.

    Args:
        regex (Pattern):
        negate (bool):
        *values (str):

    Returns:

    """
    return any(v and regex.search(v) for v in values) != negate


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
