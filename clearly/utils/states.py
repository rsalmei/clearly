"""Simulates worker states like celery tasks' states module."""

OFFLINE = 'OFFLINE'
ONLINE = 'ONLINE'
HEARTBEAT = 'HEARTBEAT'

ALL_STATES = frozenset((OFFLINE, ONLINE, HEARTBEAT))

# from celery Worker.type
TYPES = {
    'worker-offline': OFFLINE,
    'worker-online': ONLINE,
    'worker-heartbeat': HEARTBEAT,
}
