from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

import pytest

from clearly.client.code_highlighter import typed_code
from clearly.utils.safe_compiler import CallDescriptor


@pytest.mark.parametrize('obj, text', [
    # literals
    (1, '1'),
    ('1', "'1'"),
    (True, 'True'),
    (False, 'False'),
    (None, 'None'),

    # string special cases
    ("'roger'", "\"'roger'\""),
    ('"roger"', '\'"roger"\''),
    ('"roger".\'io\'', '\'"roger".\\\'io\\\'\''),

    # simple tuples
    ((), '()'),
    ((1,), '(1,)'),
    (('1',), "('1',)"),
    ((True,), "(True,)"),
    ((None,), "(None,)"),
    (('1', 2, False, None), "('1', 2, False, None)"),

    # simple lists
    ([], '[]'),
    ([1], '[1]'),
    (['1'], "['1']"),
    ([True], '[True]'),
    ([None], '[None]'),
    (['1', 2, False, None], "['1', 2, False, None]"),

    # simple sets
    ({1}, '{1}'),
    ({'1'}, "{'1'}"),
    ({True}, '{True}'),
    ({None}, '{None}'),
    ({'1', 2, False, None}, "{'1', 2, False, None}"),  # deterministic sorted

    # simple dicts
    ({}, '{}'),
    ({1: 2}, '{1: 2}'),
    ({'1': 2}, "{'1': 2}"),
    ({1: '2'}, "{1: '2'}"),
    ({'1': '2'}, "{'1': '2'}"),
    ({True: False}, "{True: False}"),
    ({None: None}, "{None: None}"),
    (OrderedDict((('1', 2), (False, None))), "{'1': 2, False: None}"),  # deterministic

    # unicode
    ('rogério', "'rogério'"),
    (('á', 'ç'), "('á', 'ç')"),
    ({'ñ', 'ô'}, "{'ñ', 'ô'}"),
    ({'ì': 'ü'}, "{'ì': 'ü'}"),

    # complex structures
    ((1, (2, True, {5, 4}), ['ba', 'b'], {1: 2}), "(1, (2, True, {4, 5}), ['ba', 'b'], {1: 2})"),
    ([1, (2, 3), {'ok': True}], "[1, (2, 3), {'ok': True}]"),
    (OrderedDict((((1, 2), ['a', 'b']), (True, {5, 6, 7}))),
     "{(1, 2): ['a', 'b'], True: {5, 6, 7}}"),

    # repr fallback
    (datetime(2018, 1, 1), 'datetime.datetime(2018, 1, 1, 0, 0)'),
    (Decimal('1.23'), "Decimal('1.23')"),

    # functions
    (CallDescriptor('rogerio', None, None), 'rogerio()'),
    (CallDescriptor('datetime', (2018, 1, 1), None), 'datetime(2018, 1, 1)'),
    (CallDescriptor('datetime.timedelta', None, {'secs': 1}), 'datetime.timedelta(secs=1)'),
    ((1, CallDescriptor('f', (1,), None), CallDescriptor('g', None, {'x': 2})),
     '(1, f(1), g(x=2))'),
    (['a', CallDescriptor('m.n', ('1',), None)], "['a', m.n('1')]"),
    ({True, CallDescriptor('f', (False,), None)}, '{f(False), True}'),
    ({None: CallDescriptor('f', None, {'param': None})}, '{None: f(param=None)}'),

    # complex functions
    (CallDescriptor('rogerio', ((1, 2), {'name': 'ok'}), {'dry_run': True}),
     "rogerio((1, 2), {'name': 'ok'}, dry_run=True)"),
    (CallDescriptor('call', None,
                    OrderedDict((('params', CallDescriptor('get_all', None, {'name': 'ok'})),
                                 ('ignore', ['False'])))),
     "call(params=get_all(name='ok'), ignore=['False'])"),
    ((CallDescriptor('Decimal', ('3.50',), None),
      [CallDescriptor('f1', (True,), {'ok': 0}),
       CallDescriptor('f2', None, {'ignore': {'y', 'x'}})]),
     "(Decimal('3.50'), [f1(True, ok=0), f2(ignore={'x', 'y'})])"),
])
def test_code_highlighter_generic(obj, text, strip_colors):
    generated = typed_code(obj)
    assert strip_colors(generated) == text
