from datetime import datetime

from .worker import function_test

function_test.delay(0, tuples=(1, 2, 3), lists=[1, 2, 3], dicts={'mess': None, True: 'clearly'})
function_test.delay(0, tuples=(1, True, {'mess': None}),
                    lists=[(1, 'rogério'), datetime.now()],
                    sets={1.1, False},
                    mixed={('any', 123): ['nice', 'huh?'], ('other', True): frozenset('abc')})
function_test.delay(50, something_wrong=True, smell={'all'}, can_handle=[])
