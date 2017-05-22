# coding=utf-8
from __future__ import unicode_literals

import six

from .safe_compiler import CallDescriptor
from .utils.colors import colors

SEPARATOR = colors.RED(', ')
KWARGS_SEPARATOR = colors.RED('=')
DICT_SEPARATOR = colors.RED(': ')
NONE = colors.CYAN('None')


def typed_text(p, wrap=True, kdict=False):
    if p is None:
        return NONE

    if isinstance(p, bool):
        return colors.CYAN(force_text(p))

    if isinstance(p, (str, unicode)):
        return colors.YELLOW("'{}'".format(force_text(p)))

    if isinstance(p, (int, long, float)):
        return colors.GREEN(force_text(p))

    if isinstance(p, CallDescriptor):
        fargs = typed_text(p.args, wrap=False) if p.args else ''
        if p.kwargs:
            if p.args:
                fargs += SEPARATOR
            fargs += typed_text(p.kwargs, wrap=False, kdict=True)
        return '{}({})'.format(force_text(p.name), fargs)

    if isinstance(p, (list, tuple, set)):
        if wrap:
            f = '[{}]' if isinstance(p, list) \
                else '({})' if isinstance(p, tuple) else '{{{}}}'
        else:
            f = '{}'
        return f.format(SEPARATOR.join(typed_text(x) for x in p))

    if isinstance(p, dict):
        f = '{{{}}}' if wrap else '{}'
        if kdict:
            key = lambda k: colors.ORANGE(k)
            sep = KWARGS_SEPARATOR
        else:
            key = lambda k: typed_text(k)
            sep = DICT_SEPARATOR
        return f.format(
            SEPARATOR.join('{}{}{}'.format(key(k), sep,
                                           typed_text(v))
                           for k, v in p.items()))

    return force_text(repr(p))


def force_text(s, encoding='utf-8', errors='strict'):
    """Based on the django.text.encoding.force_text.
    
    """
    if isinstance(s, six.text_type):
        return s
    if not isinstance(s, six.string_types):
        if hasattr(s, '__unicode__'):
            s = s.__unicode__()
        else:
            s = six.text_type(bytes(s), encoding, errors)
    else:
        s = six.text_type(s, encoding, errors)
    return s
