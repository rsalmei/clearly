from typing import List, TypeVar

C = TypeVar('C')  # how to constrain to only the closure below?


def color_factory(color_code: str) -> C:
    def apply(text: str, format_spec: str = '') -> str:
        return color_code + format(text, format_spec) + '\033[0m'

    def mix(*colors: C) -> List[C]:
        return [color_factory(c.color_code + color_code) for c in colors]

    apply.mix, apply.color_code = mix, color_code
    return apply


class Colors:
    BLUE = color_factory('\033[94m')
    GREEN = color_factory('\033[92m')
    YELLOW = color_factory('\033[93m')
    RED = color_factory('\033[91m')
    MAGENTA = color_factory('\033[95m')
    CYAN = color_factory('\033[96m')
    ORANGE = color_factory('\033[38;5;208m')

    BOLD = color_factory('\033[1m')
    DIM = color_factory('\033[2m')

    BLUE_BOLD, BLUE_DIM = BLUE.mix(BOLD, DIM)
    GREEN_BOLD, GREEN_DIM = GREEN.mix(BOLD, DIM)
    YELLOW_BOLD, YELLOW_DIM = YELLOW.mix(BOLD, DIM)
    RED_BOLD, RED_DIM = RED.mix(BOLD, DIM)
    MAGENTA_BOLD, MAGENTA_DIM = MAGENTA.mix(BOLD, DIM)
    CYAN_BOLD, CYAN_DIM = CYAN.mix(BOLD, DIM)
    ORANGE_BOLD, ORANGE_DIM = ORANGE.mix(BOLD, DIM)
