import ast
import re
from collections import OrderedDict, namedtuple
from typing import Any, Match

CallDescriptor = namedtuple('CallDescriptor', 'name args kwargs')
NON_PRINTABLE_PATTERN = re.compile('[\x00-\x1f]')


def safe_compile_text(txt: str, raises: bool = False) -> Any:
    """Generate actual objects from string representations. It internally uses
    python's ast (Abstract Syntax Trees), including support for safe 'calls',
    like in a repr of a datetime: `datetime.datetime(2017, 5, 20)`.
    Clearly uses this to convert params and results of the tasks, to be able to
    apply the advanced syntax coloring scheme seen on the Client.

    Other frameworks were not up to the task, as Clearly have some non-standard
    needs. I wanted a representation that could effectively be copied and pasted
    into a python REPL, without any changes and that would work! Which is a
    challenge to make it support arbitrary python objects...
    For example, on one hand Clearly have dicts which represent keyword arguments,
    and will show them just like a function or task would be called with, using the
    key=value notation. On the other hand, dicts in other roles would be rendered
    with the usual {key: value} notation!
    
    Also, it's worth saying that this is safe. I do not use "eval" command
    at all, which is potentially dangerous. This tool compiles the python
    objects received to an Abstract Syntax Tree, and recursively extracts
    the safe parts. Any calls or attribute lookups are returned as descriptors
    or strings, never being executed! And their parameters _will_ be analysed,
    and correctly syntax colored!

    Args:
        txt: the text
        raises: if True, raises an exception in case of error, ignores otherwise
    """

    def _convert(node):
        if isinstance(node, ast.Tuple):
            return tuple(map(_convert, node.elts))

        if isinstance(node, ast.List):
            return list(map(_convert, node.elts))

        if isinstance(node, ast.Set):
            return set(map(_convert, node.elts))

        if isinstance(node, ast.Dict):
            return OrderedDict((_convert(k), _convert(v))
                               for k, v in zip(node.keys, node.values))

        if isinstance(node, ast.Call):
            name = _convert(node.func)
            args = tuple(map(_convert, node.args))
            if name in ('tuple', 'list', 'set'):
                if len(node.args) > 1:
                    raise ValueError('{} takes at most 1 argument'.format(name))
                params = args[0] if node.args else ()
                return tuple(params) if name == 'tuple' else \
                    list(params) if name == 'list' else \
                    set(params)
            kwargs = OrderedDict((k.arg, _convert(k.value))
                                 for k in node.keywords)
            if name == 'dict':
                return kwargs
            return CallDescriptor(name,
                                  args if args else None,
                                  kwargs if kwargs else None)

        if isinstance(node, ast.Attribute):
            return '.'.join((node.value.id, node.attr))

        try:
            return ast.literal_eval(node)
        except ValueError:
            if isinstance(node, ast.Name):
                return node.id
            return 'unsupported: {}'.format(type(node))

    txt = NON_PRINTABLE_PATTERN.sub(_encode_to_hex, txt)
    try:
        txt = ast.parse(txt, mode='eval')
    except SyntaxError:
        if raises:
            raise
        return txt

    return _convert(txt.body)


def _encode_to_hex(match: Match) -> str:
    return r'\x{0:02x}'.format(ord(match.group()))
