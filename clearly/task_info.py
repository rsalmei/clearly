# coding=utf-8
from collections import namedtuple

TaskInfo = namedtuple('TaskInfo',
                      'id name args kwargs async state result retries')
TaskInfo.__new__.__defaults__ = (None,) * 4
