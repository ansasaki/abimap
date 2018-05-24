.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
       from urllib import pathname2url
except:
       from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

ci-bootstrap: ci/bootstrap.py
	python ci/bootstrap.py

bootstrap-tests:
	@SMAP_NAME_VERSION=`python version.py`; \
	echo "Setting name and version in tests as $${SMAP_NAME_VERSION}"; \
	$(MAKE) -C tests SMAP_NAME_VERSION=$${SMAP_NAME_VERSION}

clean: clean-build clean-pyc clean-test clean-docs

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -rf tests/data

clean-docs: ## remove generated docs files
	rm -rf dist/docs
	$(MAKE) -C docs clean

lint: ## check style with flake8
	flake8 src/smap tests

test: bootstrap-tests## run tests quickly with the default Python
	pytest -vv --ignore=src/

test-all: tox.ini## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	py.test --cov=smap --cov-config .coveragerc --cov-report=term-missing -vv tests
	coverage combine --append
	coverage report
	coverage html
	$(BROWSER) htmlcov/index.html

usage: ## generate usage content by calling the program
	$(MAKE) -C docs all
	cp docs/readme.rst README.rst

docs: usage ## generate Sphinx HTML documentation, including API docs
	sphinx-build -E -b doctest docs dist/docs
	sphinx-build -E -b html docs dist/docs
	sphinx-build -b linkcheck docs dist/docs

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py install
