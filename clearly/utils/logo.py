from itertools import chain, repeat

from .. import __version__

CLEARLY_LOGO = r'''
        __                __
  _____/ /__  ____ ______/ /_  __
 / ___/ / _ \/ __ `/ ___/ / / / /
/ /__/ /  __/ /_/ / /  / / /_/ /
\___/_/\___/\__,_/_/  /_/\__, /
                        /____/
'''

SYSTEMS_LOGO = dict(
    client=r'''
      ___          __ 
 ____/ (_)__ ___  / /_
/ __/ / / -_) _ \/ __/
\__/_/_/\__/_//_/\__/ 
''',
    server=r'''
 ___ ___ _____  _____ ____
(_-</ -_) __/ |/ / -_) __/
\__/\__/_/  |___/\__/_/   
''',
)


def render(system: str) -> str:
    version = '{:^20}'.format('version {}'.format(__version__))
    lines = CLEARLY_LOGO.splitlines()[1:]
    lines[-1] = '  ' + version + '  ' + lines[-1][24:]
    max_size = max(len(line) for line in lines)

    sides = SYSTEMS_LOGO[system].splitlines()[1:]
    sides = chain(repeat('', len(lines) - len(sides) - 1), sides, repeat(''))
    lines = ['{:<{}}{}'.format(line, max_size, side) for line, side in zip(lines, sides)]
    return '\n'.join(lines)
