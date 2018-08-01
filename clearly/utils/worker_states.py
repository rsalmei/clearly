# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

"""Simulates worker states like celery tasks' states module."""

OFFLINE = 'OFFLINE'
ONLINE = 'ONLINE'

ALL_STATES = frozenset((OFFLINE, ONLINE))
