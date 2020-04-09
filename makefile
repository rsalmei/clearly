.PHONY: all install clean build release protos test ptw

# grpc related
SRC = clearly
PROTOC = python -m grpc_tools.protoc
PROTOS = $(SRC)/protos

# coverage related
COV = --cov=$(SRC) --cov-branch --cov-report=term-missing

# docker related
DOCKER_REPO   = rsalmei/clearly
VERSION_BUILD = $(shell python -c "from clearly import __version__; print(__version__)")
VERSION_MINOR = $(shell python -c "from clearly import __version__; print(__version__.rpartition('.')[0])")
VERSION_MAJOR = $(shell python -c "from clearly import __version__; print(__version__.rpartition('.')[0].partition('.')[0])")
IMAGE_BUILD = $(DOCKER_REPO):$(VERSION_BUILD)
IMAGE_MINOR = $(DOCKER_REPO):$(VERSION_MINOR)
IMAGE_MAJOR = $(DOCKER_REPO):$(VERSION_MAJOR)
IMAGE_LATEST = $(DOCKER_REPO):latest


all:
	@grep -E "^\w+:" makefile | cut -d: -f1

install:
	pip install -e .[test]

dev: install
	pip install -r requirements/dev.txt

clean: clean-build clean-pyc

clean-build:
	rm -rf build dist

clean-pyc:
	find . -type f -name *.pyc -delete

build: build-python build-docker

build-python: clean
	python setup.py sdist bdist_wheel

build-docker:
	docker build -t $(IMAGE_BUILD) -t $(IMAGE_MINOR) -t $(IMAGE_MAJOR) -t $(IMAGE_LATEST) .

release: test release-python release-docker

release-python: build-python
	twine upload dist/*

release-docker: build-docker
	echo $(IMAGE_BUILD) $(IMAGE_MINOR) $(IMAGE_MAJOR) $(IMAGE_LATEST) | xargs -n 1 docker push

protos: clean-protos
	$(PROTOC) --proto_path=$(SRC) --python_out=$(SRC) --grpc_python_out=$(SRC) $(PROTOS)/clearly.proto
	sed -i '' 's/^from protos import/from . import/' $(PROTOS)/clearly_pb2_grpc.py

clean-protos:
	rm -f $(PROTOS)/*_pb2.py $(PROTOS)/*_pb2_grpc.py

test:
	pytest $(COV)

ptw:
	ptw -- $(COV)

cov-report:
	coverage report -m
