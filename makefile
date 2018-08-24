.PHONY: clean build protos

# grpc related
SRC = clearly
PROTOC = python -m grpc_tools.protoc
PROTOS = $(SRC)/protos

# coverage related
COV = --cov=$(SRC) --cov-branch --cov-report=term-missing

all:
	@grep -E "^\w+:" makefile | cut -d: -f1

install:
	pip install -r requirements/dev.txt -r requirements/test.txt

clean: clean-build clean-pyc

clean-build:
	rm -rf build dist

clean-pyc:
	find . -type f -name *.pyc -delete

build: clean
	python setup.py sdist bdist_wheel

release: build
	twine upload dist/*

clean-protos:
	rm -f $(PROTOS)/*_pb2.py $(PROTOS)/*_pb2_grpc.py

protos: clean-protos
	$(PROTOC) --proto_path=$(SRC) --python_out=$(SRC) --grpc_python_out=$(SRC) $(PROTOS)/clearly.proto
	sed -i '' 's/^from protos import/from . import/' $(PROTOS)/clearly_pb2_grpc.py

test:
	pytest $(COV)

ptw:
	ptw -- $(COV)

cov-report:
	coverage report -m
