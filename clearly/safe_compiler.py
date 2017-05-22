# coding=utf-8
from __future__ import unicode_literals

from ast import *

from collections import OrderedDict, namedtuple

CallDescriptor = namedtuple('CallDescriptor', 'name args kwargs')


def safe_compile_text(txt):
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
    """

    def _convert(node):
        if isinstance(node, Tuple):
            return tuple(map(_convert, node.elts))

        if isinstance(node, List):
            return list(map(_convert, node.elts))

        if isinstance(node, Set):
            return set(map(_convert, node.elts))

        if isinstance(node, Dict):
            return OrderedDict((_convert(k), _convert(v)) for k, v
                               in zip(node.keys, node.values))

        if isinstance(node, Call):
            name = _convert(node.func)
            if name in ('set',):
                return set(map(_convert, node.args)[0])
            args = tuple(map(_convert, node.args))
            kwargs = OrderedDict((k.arg, _convert(k.value))
                                 for k in node.keywords)
            return CallDescriptor(_convert(node.func),
                                  args if args else None,
                                  kwargs if kwargs else None)

        if isinstance(node, Attribute):
            return '.'.join((node.value.id, node.attr))

        try:
            return literal_eval(node)
        except ValueError:
            if isinstance(node, Name):
                return node.id
            return repr(node)

    try:
        txt = parse(txt, mode='eval')
    except SyntaxError:
        return txt
    if isinstance(txt, Expression):
        txt = txt.body
    return _convert(txt)
