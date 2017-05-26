# coding=utf-8
from __future__ import unicode_literals

__author__ = 'Rogério Sampaio de Almeida'

VERSION = (0, 2, 5)  # 'major', 'minor', 'release'
__version__ = '.'.join(map(str, VERSION))

from .client import ClearlyClient

__all__ = ('__author__', '__version__', 'ClearlyClient',)

from kombu import log
import logging

log.get_logger('').setLevel(logging.ERROR)
