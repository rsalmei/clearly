"""Complements celery tasks' states module with worker states."""

OFFLINE = 'OFFLINE'
ONLINE = 'ONLINE'
HEARTBEAT = 'HEARTBEAT'

ALL_STATES = frozenset((OFFLINE, ONLINE, HEARTBEAT))

# event types from celery Worker.type
TYPES = {
    'worker-offline': OFFLINE,
    'worker-online': ONLINE,
    'worker-heartbeat': HEARTBEAT,
}
