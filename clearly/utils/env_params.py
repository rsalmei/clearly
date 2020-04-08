import logging
import os
from functools import partial
from typing import Callable, TypeVar, List

logger = logging.getLogger(__name__)

TV = TypeVar('TV', str, int, List[str])


def get_env_param(name: str, default: TV, factory: Callable[[str], TV]) -> TV:
    """Return a named environment variable cast to the correct type, or a
    default param.

    Args:
        name: the var name
        default: the default value
        factory: a function to convert the string values from env

    Returns:
        the converted value or default
    """
    value = os.getenv(name)
    try:
        return factory(value) if value else default
    except ValueError:
        logger.warning('Ignoring env var: %s=%s', name, value)
        return default


get_env_str = partial(get_env_param, factory=str)
get_env_int = partial(get_env_param, factory=int)
get_env_tuple = partial(get_env_param, factory=lambda x: tuple(x.split()))
get_env_int_tuple = partial(get_env_param, factory=lambda x: tuple(int(y) for y in x.split()))
