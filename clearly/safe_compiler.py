# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import ast
import re
from collections import OrderedDict, namedtuple

CallDescriptor = namedtuple('CallDescriptor', 'name args kwargs')
NON_PRINTABLE_PATTERN = re.compile('[\x00-\x1f]')


def safe_compile_text(txt, raises=False):
    """Based on actual ast.literal_eval, but this one supports 'calls', 
    like in a repr of a datetime: `datetime.datetime(2017, 5, 20)`.
    
    Clearly uses this to generate actual python objects of the params and 
    results of the tasks, to be able to apply the advanced syntax coloring
    scheme implemented here. Other frameworks were not up to the task, as
    Clearly needs for example, to show dicts with a keyword args notation, 
    to clearly see what the task was called with. And if there's a dict in
    the value part of said kwarg, it will be correctly rendered as a dict!
    
    Also, it's worth saying that this is safe. I do not use "eval" command
    at all, which is potentially dangerous. This tool compiles the python
    objects received to an Abstract Syntax Tree, and recursively extracts
    the safe parts. Any calls or attribute lookups are returned as descriptors
    or strings, never being executed. And their parameters _will_ be analysed,
    and correctly syntax colored!

    Args:
        txt (str): the text
        raises (bool): if True, raise an exception in case of error
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


def _encode_to_hex(match):
    return r'\x{0:02x}'.format(ord(match.group()))
