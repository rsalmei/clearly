# coding=utf-8

__author__ = 'Rogério Sampaio de Almeida'

VERSION = (0, 1, 4)  # 'major', 'minor', 'release'
__version__ = '.'.join(map(str, VERSION))

from .core import Clearly

__all__ = ('__author__', '__version__', 'Clearly',)
