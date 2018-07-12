#!/usr/bin/env bash

rm -rf build
rm -rf dist
pip install -U twine >/dev/null

python setup.py sdist bdist_wheel && twine upload dist/*
