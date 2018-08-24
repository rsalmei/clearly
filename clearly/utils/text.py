# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import six


def force_text(s, encoding='utf-8', errors='strict'):
    """Based on the django.text.encoding.force_text.

    """
    if isinstance(s, six.text_type):  # pragma: no cover
        return s
    if not isinstance(s, six.string_types):  # pragma: no cover
        if hasattr(s, '__unicode__'):
            s = s.__unicode__()
        else:
            s = six.text_type(bytes(s), encoding, errors)
    else:  # pragma: no cover
        s = six.text_type(s, encoding, errors)
    return s  # pragma: no cover
