#!/usr/bin/env bash

celery worker -A tasks -E --loglevel=info
