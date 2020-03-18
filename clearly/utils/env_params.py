import logging
import os
from functools import partial
from typing import Callable, T

logger = logging.getLogger(__name__)


def get_env_param(name: str, default: T, factory: Callable[[str], T]) -> T:
    """Get and cast a named environment variable to the correct type, given by
    the default param.

    Args:
        name: the var name
        default: the default value, which should have a constructor with str
        factory: a function to convert the str value

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
get_env_list = partial(get_env_param, factory=lambda x: x.split())
