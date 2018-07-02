import pytest

from clearly.safe_compiler import CallDescriptor, safe_compile_text


@pytest.mark.parametrize('text, obj', [
    # literals
    ('1', 1),
    ('"1"', '1'),
    ("'1'", '1'),
    ('True', True),
    ('False', False),
    ('None', None),

    # simple tuples
    ('()', ()),
    ('(1,)', (1,)),
    ('("1",)', ('1',)),
    ("('1',)", ('1',)),
    ('(True,)', (True,)),
    ('(None,)', (None,)),
    ('("1", 2, False, None)', ('1', 2, False, None)),
    ('("1", 2, False, None, )', ('1', 2, False, None)),
    ('"1", 2, False, None', ('1', 2, False, None)),

    # function tuples
    ('tuple()', ()),
    ('tuple((1,))', (1,)),
    ('tuple(("1",))', ('1',)),
    ("tuple(('1',))", ('1',)),
    ('tuple((True,))', (True,)),
    ('tuple((None,))', (None,)),
    ('tuple(("1", 2, False, None))', ('1', 2, False, None)),
    ('tuple(("1", 2, False, None, ))', ('1', 2, False, None)),

    # simple lists
    ('[]', []),
    ('[1,]', [1]),
    ('[1]', [1]),
    ('["1"]', ['1']),
    ('[True]', [True]),
    ('[None]', [None]),
    ('["1", 2, False, None]', ['1', 2, False, None]),

    # function lists
    ('list()', []),
    ('list((1,))', [1]),
    ('list(("1",))', ['1']),
    ('list((True,))', [True]),
    ('list((None,))', [None]),
    ('list(("1", 2, False, None))', ['1', 2, False, None]),
    ('list(("1", 2, False, None, ))', ['1', 2, False, None]),

    # simple sets
    ('{1,}', {1}),
    ('{1}', {1}),
    ('{"1"}', {'1'}),
    ('{True}', {True}),
    ('{None}', {None}),
    ('{"1", 2, False, None}', {'1', 2, False, None}),

    # function sets
    ('set()', set()),
    ('set((1,))', {1}),
    ('set(("1",))', {'1'}),
    ('set((True,))', {True}),
    ('set((None,))', {None}),
    ('set(("1", 2, False, None))', {'1', 2, False, None}),
    ('set(("1", 2, False, None, ))', {'1', 2, False, None}),

    # simple dicts
    ('{}', {}),
    ('{1:2,}', {1: 2}),
    ('{1:2}', {1: 2}),
    ('{"1":2}', {'1': 2}),
    ('{1:"2"}', {1: '2'}),
    ('{"1":"2"}', {'1': '2'}),
    ('{True:False}', {True: False}),
    ('{None:None}', {None: None}),
    ('{"1": 2, False: None}', {'1': 2, False: None}),

    # function dicts
    ('dict()', {}),
    ('dict(a=2)', {'a': 2}),
    ('dict(a=2,)', {'a': 2}),
    ('dict(a="ok")', {'a': 'ok'}),
    ('dict(a=False)', {'a': False}),
    ('dict(a=None)', {'a': None}),
    ('dict(a=1, b=2)', {'a': 1, 'b': 2}),
    ('dict(a=1, b="2", c=True, d=None)', {'a': 1, 'b': '2', 'c': True, 'd': None}),

    # complex structures
    ('1, (2, True, {3, 4}), ["a", "b"], {1:2}', (1, (2, True, {3, 4}), ["a", "b"], {1: 2})),
    ('[1, (2, 3), {"ok": True}]', [1, (2, 3), {"ok": True}]),
    ('{(1, 2): ["a", "b"], True: {5, 6, 7}}', {(1, 2): ["a", "b"], True: {5, 6, 7}}),

    # attributes
    ('rogerio', 'rogerio'),
    ('roger.io', 'roger.io'),

    # functions
    ('rogerio()', CallDescriptor('rogerio', None, None)),
    ('datetime(2018,1,1)', CallDescriptor('datetime', (2018, 1, 1), None)),
    ('datetime.timedelta(secs=1)', CallDescriptor('datetime.timedelta', None, {'secs': 1})),
    ('1, f(1), g(x=2)', (1, CallDescriptor('f', (1,), None), CallDescriptor('g', None, {'x': 2}))),
    ('["a", m.n("1")]', ['a', CallDescriptor('m.n', ('1',), None)]),
    ('{True, f(False)}', {True, CallDescriptor('f', (False,), None)}),
    ('{None: f(param=None)}', {None: CallDescriptor('f', None, {'param': None})}),

    # complex functions
    ('rogerio((1, 2), dict(name="ok"), dry_run=True)',
     CallDescriptor('rogerio',
                    ((1, 2), {'name': 'ok'}),
                    {'dry_run': True})),
    ('call(params=get_all(name="ok"), ignore=["False"])',
     CallDescriptor('call', None,
                    {'params': CallDescriptor('get_all', None, {'name': 'ok'}),
                     'ignore': ['False']})),

    ('decimal.Decimal("3.50"), [f1(True, ok=0), f2(ignore=set(("x", "y")))]',
     (CallDescriptor('decimal.Decimal', ('3.50',), None),
      [CallDescriptor('f1', (True,), {'ok': 0}),
       CallDescriptor('f2', None, {'ignore': {'x', 'y'}})])),
])
def test_compiler_data(text, obj):
    assert safe_compile_text(text) == obj
