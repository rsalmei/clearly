from __future__ import absolute_import, print_function, unicode_literals

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import Python3TracebackLexer


def create_highlighter():
    lexer = Python3TracebackLexer()
    formatter = Terminal256Formatter(style='native')

    def inner(tb):
        return highlight(tb, lexer, formatter)

    return inner
