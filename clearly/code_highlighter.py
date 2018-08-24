# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import six
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.python import Python3TracebackLexer

from .safe_compiler import CallDescriptor
from .utils.colors import Colors
from .utils.text import force_text

SEPARATOR = Colors.RED(', ')
KWARGS_SEPARATOR = Colors.RED('=')
DICT_SEPARATOR = Colors.RED(': ')
NONE = Colors.CYAN('None')

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    unicode
except NameError:  # pragma: no cover
    def unicode(x):
        return str(x)


def typed_code(p, wrap=True):
    if p is None:
        return NONE

    if isinstance(p, bool):
        return Colors.CYAN(str(p))

    if isinstance(p, six.string_types):
        p = force_text(p)
        if "'" in p and '"' not in p:
            escape = '"'
        else:
            escape = "'"
            p = p.replace("'", "\\'")
        return Colors.YELLOW('{c}{p}{c}'.format(p=p, c=escape))

    if isinstance(p, six.integer_types + (float,)):
        return Colors.GREEN(str(p))

    if isinstance(p, CallDescriptor):
        func_args = typed_code(p.args, wrap=False) if p.args else ''
        if p.kwargs:
            if p.args:
                func_args += SEPARATOR
            func_args += typed_code(p.kwargs, wrap=False)
        return '{}({})'.format(force_text(p.name), func_args)

    if isinstance(p, list):
        f = '[{}]' if wrap else '{}'
        return f.format(SEPARATOR.join(typed_code(x) for x in p))

    if isinstance(p, set):
        return '{{{}}}'.format(typed_code(sorted(p, key=lambda x: unicode(x)), wrap=False))

    if isinstance(p, tuple):
        if wrap:
            f = '({})' if len(p) != 1 else '({},)'
        else:
            f = '{}'
        return f.format(SEPARATOR.join(typed_code(x) for x in p))

    if isinstance(p, dict):
        if wrap:
            f = '{{{}}}'
            sep = DICT_SEPARATOR

            def key(k):
                return typed_code(k)
        else:
            f = '{}'
            sep = KWARGS_SEPARATOR

            def key(k):
                return Colors.ORANGE(k)

        return f.format(
            SEPARATOR.join('{}{}{}'.format(key(k), sep, typed_code(v))
                           for k, v in p.items()))

    return force_text(repr(p))


def create_traceback_highlighter():
    lexer = Python3TracebackLexer()
    formatter = Terminal256Formatter(style='native')

    def inner(tb):
        return highlight(tb, lexer, formatter)

    return inner
