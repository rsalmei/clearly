# coding=utf-8

__author__ = 'Rogério Sampaio de Almeida'

VERSION = (0, 1, 0)  # 'major', 'minor', 'release'
__version__ = '{}.{}.{}'.format(*VERSION)

from .core import Clearly

__all__ = ('__author__', '__version__', 'Clearly',)
