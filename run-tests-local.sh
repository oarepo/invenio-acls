#!/usr/bin/env bash
##
## Copyright (c) 2019 UCT Prague.
## 
## run-tests-local.sh is part of Invenio Explicit ACLs 
## (see https://github.com/oarepo/invenio-explicit-acls).
## 
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.
##

set -e -o pipefail

test -d /tmp/workdir && rm -r /tmp/workdir

rsync -a --exclude __pycache__ /invenio-explicit-acls/ /tmp/workdir
apt install rabbitmq-server
/etc/init.d/rabbitmq-server start

cd /tmp/workdir

pydocstyle invenio_explicit_acls tests docs
isort -rc -c -df
check-manifest --ignore ".travis-*,docs/_build*"

pip install -e .

sphinx-build -qnNW docs docs/_build/html

sudo -u es /tmp/elasticsearch/bin/elasticsearch &
sleep 10

rsync -a --exclude __pycache__ /invenio-explicit-acls/ /tmp/workdir && python setup.py test

#  docker run -it --entrypoint /bin/bash -v $PWD:/invenio-explicit-acls invenio-acls_travis
# to run locally in docker:
# reset; rsync -a --delete --exclude __pycache__ /invenio-explicit-acls/ /tmp/workdir && python setup.py build; pytest -s tests/test_no_acl.py
# to run single test
# reset; rsync -a --exclude __pycache__ /invenio-explicit-acls/ /tmp/workdir && pytest tests/test_default_acl_unittests.py

