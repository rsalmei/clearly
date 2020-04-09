from typing import Any, Callable

from ..utils.colors import Colors
from ..utils.safe_compiler import CallDescriptor

SEPARATOR = Colors.RED(', ')
KWARGS_SEPARATOR = Colors.RED('=')
DICT_SEPARATOR = Colors.RED(': ')
NONE = Colors.CYAN('None')


def typed_code(p: Any, wrap: bool = True) -> str:
    if p is None:
        return NONE

    if isinstance(p, bool):
        return Colors.CYAN(str(p))

    if isinstance(p, str):
        if "'" in p and '"' not in p:
            escape = '"'
        else:
            escape = "'"
            p = p.replace("'", "\\'")
        return Colors.YELLOW('{c}{p}{c}'.format(p=p, c=escape))

    if isinstance(p, (int, float, complex)):
        return Colors.GREEN(str(p))

    if isinstance(p, CallDescriptor):
        func_args = typed_code(p.args, wrap=False) if p.args else ''
        if p.kwargs:
            if p.args:
                func_args += SEPARATOR
            func_args += typed_code(p.kwargs, wrap=False)
        return '{}({})'.format(p.name, func_args)

    if isinstance(p, list):
        f = '[{}]' if wrap else '{}'
        return f.format(SEPARATOR.join(typed_code(x) for x in p))

    if isinstance(p, set):
        return '{{{}}}'.format(typed_code(sorted(p, key=lambda x: str(x)), wrap=False))

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

    return repr(p)


def traceback_highlighter_factory() -> Callable[[str], str]:  # pragma: no cover
    from pygments.lexers.python import PythonTracebackLexer
    lexer = PythonTracebackLexer()
    from pygments.formatters.terminal256 import Terminal256Formatter
    formatter = Terminal256Formatter(style='native')

    def inner(tb):
        return highlight(tb, lexer, formatter)

    from pygments import highlight
    return inner
