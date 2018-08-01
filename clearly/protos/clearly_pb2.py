# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/clearly.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='protos/clearly.proto',
  package='',
  syntax='proto3',
  serialized_pb=_b('\n\x14protos/clearly.proto\"\xc3\x01\n\x0bTaskMessage\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0brouting_key\x18\x02 \x01(\t\x12\x0c\n\x04uuid\x18\x03 \x01(\t\x12\x0f\n\x07retries\x18\x04 \x01(\x05\x12\x0c\n\x04\x61rgs\x18\x05 \x01(\t\x12\x0e\n\x06kwargs\x18\x06 \x01(\t\x12\x0e\n\x06result\x18\x07 \x01(\t\x12\x11\n\ttraceback\x18\x08 \x01(\t\x12\x11\n\ttimestamp\x18\t \x01(\x02\x12\r\n\x05state\x18\n \x01(\t\x12\x0f\n\x07\x63reated\x18\x0b \x01(\x08\"\xd9\x01\n\rWorkerMessage\x12\x10\n\x08hostname\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\x05\x12\x0e\n\x06sw_sys\x18\x03 \x01(\t\x12\x10\n\x08sw_ident\x18\x04 \x01(\t\x12\x0e\n\x06sw_ver\x18\x05 \x01(\t\x12\x0f\n\x07loadavg\x18\x06 \x03(\x02\x12\x11\n\tprocessed\x18\x07 \x01(\x05\x12\r\n\x05\x61live\x18\x08 \x01(\x08\x12\x0c\n\x04\x66req\x18\t \x01(\x02\x12\x16\n\x0elast_heartbeat\x18\n \x01(\x02\x12\r\n\x05state\x18\x0b \x01(\t\x12\x0f\n\x07\x63reated\x18\x0c \x01(\x08\"_\n\x14RealtimeEventMessage\x12\x1c\n\x04task\x18\x01 \x01(\x0b\x32\x0c.TaskMessageH\x00\x12 \n\x06worker\x18\x02 \x01(\x0b\x32\x0e.WorkerMessageH\x00\x42\x07\n\x05\x65vent\"&\n\x10SeenTasksMessage\x12\x12\n\ntask_types\x18\x01 \x03(\t\"_\n\x0cStatsMessage\x12\x12\n\ntask_count\x18\x01 \x01(\x05\x12\x13\n\x0b\x65vent_count\x18\x02 \x01(\x05\x12\x11\n\tlen_tasks\x18\x03 \x01(\x05\x12\x13\n\x0blen_workers\x18\x04 \x01(\x05\"0\n\rPatternFilter\x12\x0f\n\x07pattern\x18\x01 \x01(\t\x12\x0e\n\x06negate\x18\x02 \x01(\x08\"`\n\x0e\x43\x61ptureRequest\x12%\n\rtasks_capture\x18\x01 \x01(\x0b\x32\x0e.PatternFilter\x12\'\n\x0fworkers_capture\x18\x02 \x01(\x0b\x32\x0e.PatternFilter\"B\n\x16\x46ilterTasksTypeRequest\x12\x11\n\ttask_type\x18\x01 \x01(\t\x12\x15\n\rstate_pattern\x18\x02 \x01(\t\"J\n\x18\x46ilterTasksWorkerRequest\x12\x17\n\x0fworker_hostname\x18\x01 \x01(\t\x12\x15\n\rstate_pattern\x18\x02 \x01(\t\"Q\n\x12\x46ilterTasksRequest\x12$\n\x0ctasks_filter\x18\x01 \x01(\x0b\x32\x0e.PatternFilter\x12\x15\n\rstate_pattern\x18\x02 \x01(\t\">\n\x14\x46ilterWorkersRequest\x12&\n\x0eworkers_filter\x18\x01 \x01(\x0b\x32\x0e.PatternFilter\"$\n\x0f\x46indTaskRequest\x12\x11\n\ttask_uuid\x18\x01 \x01(\t\"\x07\n\x05\x45mpty2\xdc\x03\n\rClearlyServer\x12<\n\x10\x63\x61pture_realtime\x12\x0f.CaptureRequest\x1a\x15.RealtimeEventMessage0\x01\x12?\n\x14\x66ilter_tasks_by_type\x12\x17.FilterTasksTypeRequest\x1a\x0c.TaskMessage0\x01\x12\x43\n\x16\x66ilter_tasks_by_worker\x12\x19.FilterTasksWorkerRequest\x1a\x0c.TaskMessage0\x01\x12\x33\n\x0c\x66ilter_tasks\x12\x13.FilterTasksRequest\x1a\x0c.TaskMessage0\x01\x12\x39\n\x0e\x66ilter_workers\x12\x15.FilterWorkersRequest\x1a\x0e.WorkerMessage0\x01\x12+\n\tfind_task\x12\x10.FindTaskRequest\x1a\x0c.TaskMessage\x12\'\n\nseen_tasks\x12\x06.Empty\x1a\x11.SeenTasksMessage\x12\x1d\n\x0breset_tasks\x12\x06.Empty\x1a\x06.Empty\x12\"\n\tget_stats\x12\x06.Empty\x1a\r.StatsMessageb\x06proto3')
)




_TASKMESSAGE = _descriptor.Descriptor(
  name='TaskMessage',
  full_name='TaskMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='TaskMessage.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='routing_key', full_name='TaskMessage.routing_key', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='uuid', full_name='TaskMessage.uuid', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='retries', full_name='TaskMessage.retries', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='args', full_name='TaskMessage.args', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='kwargs', full_name='TaskMessage.kwargs', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='result', full_name='TaskMessage.result', index=6,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='traceback', full_name='TaskMessage.traceback', index=7,
      number=8, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='TaskMessage.timestamp', index=8,
      number=9, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='state', full_name='TaskMessage.state', index=9,
      number=10, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='created', full_name='TaskMessage.created', index=10,
      number=11, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=25,
  serialized_end=220,
)


_WORKERMESSAGE = _descriptor.Descriptor(
  name='WorkerMessage',
  full_name='WorkerMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hostname', full_name='WorkerMessage.hostname', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pid', full_name='WorkerMessage.pid', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sw_sys', full_name='WorkerMessage.sw_sys', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sw_ident', full_name='WorkerMessage.sw_ident', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sw_ver', full_name='WorkerMessage.sw_ver', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='loadavg', full_name='WorkerMessage.loadavg', index=5,
      number=6, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='processed', full_name='WorkerMessage.processed', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='alive', full_name='WorkerMessage.alive', index=7,
      number=8, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='freq', full_name='WorkerMessage.freq', index=8,
      number=9, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='last_heartbeat', full_name='WorkerMessage.last_heartbeat', index=9,
      number=10, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='state', full_name='WorkerMessage.state', index=10,
      number=11, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='created', full_name='WorkerMessage.created', index=11,
      number=12, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=223,
  serialized_end=440,
)


_REALTIMEEVENTMESSAGE = _descriptor.Descriptor(
  name='RealtimeEventMessage',
  full_name='RealtimeEventMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='task', full_name='RealtimeEventMessage.task', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='worker', full_name='RealtimeEventMessage.worker', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='event', full_name='RealtimeEventMessage.event',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=442,
  serialized_end=537,
)


_SEENTASKSMESSAGE = _descriptor.Descriptor(
  name='SeenTasksMessage',
  full_name='SeenTasksMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='task_types', full_name='SeenTasksMessage.task_types', index=0,
      number=1, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=539,
  serialized_end=577,
)


_STATSMESSAGE = _descriptor.Descriptor(
  name='StatsMessage',
  full_name='StatsMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='task_count', full_name='StatsMessage.task_count', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='event_count', full_name='StatsMessage.event_count', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='len_tasks', full_name='StatsMessage.len_tasks', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='len_workers', full_name='StatsMessage.len_workers', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=579,
  serialized_end=674,
)


_PATTERNFILTER = _descriptor.Descriptor(
  name='PatternFilter',
  full_name='PatternFilter',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='pattern', full_name='PatternFilter.pattern', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='negate', full_name='PatternFilter.negate', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=676,
  serialized_end=724,
)


_CAPTUREREQUEST = _descriptor.Descriptor(
  name='CaptureRequest',
  full_name='CaptureRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='tasks_capture', full_name='CaptureRequest.tasks_capture', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='workers_capture', full_name='CaptureRequest.workers_capture', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=726,
  serialized_end=822,
)


_FILTERTASKSTYPEREQUEST = _descriptor.Descriptor(
  name='FilterTasksTypeRequest',
  full_name='FilterTasksTypeRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='task_type', full_name='FilterTasksTypeRequest.task_type', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='state_pattern', full_name='FilterTasksTypeRequest.state_pattern', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=824,
  serialized_end=890,
)


_FILTERTASKSWORKERREQUEST = _descriptor.Descriptor(
  name='FilterTasksWorkerRequest',
  full_name='FilterTasksWorkerRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='worker_hostname', full_name='FilterTasksWorkerRequest.worker_hostname', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='state_pattern', full_name='FilterTasksWorkerRequest.state_pattern', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=892,
  serialized_end=966,
)


_FILTERTASKSREQUEST = _descriptor.Descriptor(
  name='FilterTasksRequest',
  full_name='FilterTasksRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='tasks_filter', full_name='FilterTasksRequest.tasks_filter', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='state_pattern', full_name='FilterTasksRequest.state_pattern', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=968,
  serialized_end=1049,
)


_FILTERWORKERSREQUEST = _descriptor.Descriptor(
  name='FilterWorkersRequest',
  full_name='FilterWorkersRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='workers_filter', full_name='FilterWorkersRequest.workers_filter', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1051,
  serialized_end=1113,
)


_FINDTASKREQUEST = _descriptor.Descriptor(
  name='FindTaskRequest',
  full_name='FindTaskRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='task_uuid', full_name='FindTaskRequest.task_uuid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1115,
  serialized_end=1151,
)


_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1153,
  serialized_end=1160,
)

_REALTIMEEVENTMESSAGE.fields_by_name['task'].message_type = _TASKMESSAGE
_REALTIMEEVENTMESSAGE.fields_by_name['worker'].message_type = _WORKERMESSAGE
_REALTIMEEVENTMESSAGE.oneofs_by_name['event'].fields.append(
  _REALTIMEEVENTMESSAGE.fields_by_name['task'])
_REALTIMEEVENTMESSAGE.fields_by_name['task'].containing_oneof = _REALTIMEEVENTMESSAGE.oneofs_by_name['event']
_REALTIMEEVENTMESSAGE.oneofs_by_name['event'].fields.append(
  _REALTIMEEVENTMESSAGE.fields_by_name['worker'])
_REALTIMEEVENTMESSAGE.fields_by_name['worker'].containing_oneof = _REALTIMEEVENTMESSAGE.oneofs_by_name['event']
_CAPTUREREQUEST.fields_by_name['tasks_capture'].message_type = _PATTERNFILTER
_CAPTUREREQUEST.fields_by_name['workers_capture'].message_type = _PATTERNFILTER
_FILTERTASKSREQUEST.fields_by_name['tasks_filter'].message_type = _PATTERNFILTER
_FILTERWORKERSREQUEST.fields_by_name['workers_filter'].message_type = _PATTERNFILTER
DESCRIPTOR.message_types_by_name['TaskMessage'] = _TASKMESSAGE
DESCRIPTOR.message_types_by_name['WorkerMessage'] = _WORKERMESSAGE
DESCRIPTOR.message_types_by_name['RealtimeEventMessage'] = _REALTIMEEVENTMESSAGE
DESCRIPTOR.message_types_by_name['SeenTasksMessage'] = _SEENTASKSMESSAGE
DESCRIPTOR.message_types_by_name['StatsMessage'] = _STATSMESSAGE
DESCRIPTOR.message_types_by_name['PatternFilter'] = _PATTERNFILTER
DESCRIPTOR.message_types_by_name['CaptureRequest'] = _CAPTUREREQUEST
DESCRIPTOR.message_types_by_name['FilterTasksTypeRequest'] = _FILTERTASKSTYPEREQUEST
DESCRIPTOR.message_types_by_name['FilterTasksWorkerRequest'] = _FILTERTASKSWORKERREQUEST
DESCRIPTOR.message_types_by_name['FilterTasksRequest'] = _FILTERTASKSREQUEST
DESCRIPTOR.message_types_by_name['FilterWorkersRequest'] = _FILTERWORKERSREQUEST
DESCRIPTOR.message_types_by_name['FindTaskRequest'] = _FINDTASKREQUEST
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

TaskMessage = _reflection.GeneratedProtocolMessageType('TaskMessage', (_message.Message,), dict(
  DESCRIPTOR = _TASKMESSAGE,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:TaskMessage)
  ))
_sym_db.RegisterMessage(TaskMessage)

WorkerMessage = _reflection.GeneratedProtocolMessageType('WorkerMessage', (_message.Message,), dict(
  DESCRIPTOR = _WORKERMESSAGE,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:WorkerMessage)
  ))
_sym_db.RegisterMessage(WorkerMessage)

RealtimeEventMessage = _reflection.GeneratedProtocolMessageType('RealtimeEventMessage', (_message.Message,), dict(
  DESCRIPTOR = _REALTIMEEVENTMESSAGE,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:RealtimeEventMessage)
  ))
_sym_db.RegisterMessage(RealtimeEventMessage)

SeenTasksMessage = _reflection.GeneratedProtocolMessageType('SeenTasksMessage', (_message.Message,), dict(
  DESCRIPTOR = _SEENTASKSMESSAGE,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:SeenTasksMessage)
  ))
_sym_db.RegisterMessage(SeenTasksMessage)

StatsMessage = _reflection.GeneratedProtocolMessageType('StatsMessage', (_message.Message,), dict(
  DESCRIPTOR = _STATSMESSAGE,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:StatsMessage)
  ))
_sym_db.RegisterMessage(StatsMessage)

PatternFilter = _reflection.GeneratedProtocolMessageType('PatternFilter', (_message.Message,), dict(
  DESCRIPTOR = _PATTERNFILTER,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:PatternFilter)
  ))
_sym_db.RegisterMessage(PatternFilter)

CaptureRequest = _reflection.GeneratedProtocolMessageType('CaptureRequest', (_message.Message,), dict(
  DESCRIPTOR = _CAPTUREREQUEST,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:CaptureRequest)
  ))
_sym_db.RegisterMessage(CaptureRequest)

FilterTasksTypeRequest = _reflection.GeneratedProtocolMessageType('FilterTasksTypeRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILTERTASKSTYPEREQUEST,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:FilterTasksTypeRequest)
  ))
_sym_db.RegisterMessage(FilterTasksTypeRequest)

FilterTasksWorkerRequest = _reflection.GeneratedProtocolMessageType('FilterTasksWorkerRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILTERTASKSWORKERREQUEST,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:FilterTasksWorkerRequest)
  ))
_sym_db.RegisterMessage(FilterTasksWorkerRequest)

FilterTasksRequest = _reflection.GeneratedProtocolMessageType('FilterTasksRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILTERTASKSREQUEST,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:FilterTasksRequest)
  ))
_sym_db.RegisterMessage(FilterTasksRequest)

FilterWorkersRequest = _reflection.GeneratedProtocolMessageType('FilterWorkersRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILTERWORKERSREQUEST,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:FilterWorkersRequest)
  ))
_sym_db.RegisterMessage(FilterWorkersRequest)

FindTaskRequest = _reflection.GeneratedProtocolMessageType('FindTaskRequest', (_message.Message,), dict(
  DESCRIPTOR = _FINDTASKREQUEST,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:FindTaskRequest)
  ))
_sym_db.RegisterMessage(FindTaskRequest)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), dict(
  DESCRIPTOR = _EMPTY,
  __module__ = 'protos.clearly_pb2'
  # @@protoc_insertion_point(class_scope:Empty)
  ))
_sym_db.RegisterMessage(Empty)



_CLEARLYSERVER = _descriptor.ServiceDescriptor(
  name='ClearlyServer',
  full_name='ClearlyServer',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=1163,
  serialized_end=1639,
  methods=[
  _descriptor.MethodDescriptor(
    name='capture_realtime',
    full_name='ClearlyServer.capture_realtime',
    index=0,
    containing_service=None,
    input_type=_CAPTUREREQUEST,
    output_type=_REALTIMEEVENTMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='filter_tasks_by_type',
    full_name='ClearlyServer.filter_tasks_by_type',
    index=1,
    containing_service=None,
    input_type=_FILTERTASKSTYPEREQUEST,
    output_type=_TASKMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='filter_tasks_by_worker',
    full_name='ClearlyServer.filter_tasks_by_worker',
    index=2,
    containing_service=None,
    input_type=_FILTERTASKSWORKERREQUEST,
    output_type=_TASKMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='filter_tasks',
    full_name='ClearlyServer.filter_tasks',
    index=3,
    containing_service=None,
    input_type=_FILTERTASKSREQUEST,
    output_type=_TASKMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='filter_workers',
    full_name='ClearlyServer.filter_workers',
    index=4,
    containing_service=None,
    input_type=_FILTERWORKERSREQUEST,
    output_type=_WORKERMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='find_task',
    full_name='ClearlyServer.find_task',
    index=5,
    containing_service=None,
    input_type=_FINDTASKREQUEST,
    output_type=_TASKMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='seen_tasks',
    full_name='ClearlyServer.seen_tasks',
    index=6,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_SEENTASKSMESSAGE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='reset_tasks',
    full_name='ClearlyServer.reset_tasks',
    index=7,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_EMPTY,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='get_stats',
    full_name='ClearlyServer.get_stats',
    index=8,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_STATSMESSAGE,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_CLEARLYSERVER)

DESCRIPTOR.services_by_name['ClearlyServer'] = _CLEARLYSERVER

# @@protoc_insertion_point(module_scope)