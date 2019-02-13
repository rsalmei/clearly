"""Simulates worker states like celery tasks' states module."""

OFFLINE = 'OFFLINE'
ONLINE = 'ONLINE'

ALL_STATES = frozenset((OFFLINE, ONLINE))
