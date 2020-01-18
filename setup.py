#
# Copyright (c) 2019 UCT Prague.
#
# setup.py is part of Invenio Explicit ACLs
# (see https://github.com/oarepo/invenio-explicit-acls).
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""Data model for CIS theses repository"""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
OAREPO_VERSION = os.environ.get('OAREPO_VERSION', '3.1.1')

tests_require = [
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
        'sphinxcontrib-httpdomain>=1.7.0'
    ],
    'tests': [
        *tests_require,
        'oarepo[tests]~={version}'.format(
            version=OAREPO_VERSION)],
    'tests-es7': [
        *tests_require,
        'oarepo[tests-es7]~={version}'.format(
            version=OAREPO_VERSION)],
}

setup_requires = [
    'pytest-runner>=2.6.2',
]

install_requires = [
    "invenio-oarepo-invenio-model>=1.2"
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_explicit_acls', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-explicit-acls',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='invenio-explicit-acls Invenio declarative ACL',
    license='MIT',
    author='CIS UCT Prague',
    author_email='simeki@vscht.cz',
    url='https://github.com/oarepo/invenio-explicit-acls',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_db.models': [
            'invenio_explicit_acls = invenio_explicit_acls.models',
            'invenio_explicit_acls_actors = invenio_explicit_acls.actors',
            'invenio_explicit_acls_acls = invenio_explicit_acls.acls',
        ],
        'invenio_base.apps': [
            'invenio_explicit_acls = invenio_explicit_acls.ext:InvenioExplicitAcls',
        ],
        'invenio_base.api_apps': [
            'invenio_explicit_acls = invenio_explicit_acls.ext:InvenioExplicitAcls',
        ],
        'invenio_admin.views': [
            'elasticsearch_aclset_adminview = invenio_explicit_acls.admin:elasticsearch_aclset_adminview',
            'id_aclset_adminview = invenio_explicit_acls.admin:id_aclset_adminview',
            'default_aclset_adminview = invenio_explicit_acls.admin:default_aclset_adminview',
            'propertyvalueacl_aclset_adminview = invenio_explicit_acls.admin:propertyvalueacl_aclset_adminview',
            'useractor_aclset_adminview = invenio_explicit_acls.admin:useractor_aclset_adminview',
            'roleactor_aclset_adminview = invenio_explicit_acls.admin:roleactor_aclset_adminview',
            'recorduseractor_aclset_adminview = invenio_explicit_acls.admin:recorduseractor_aclset_adminview',
            'recordroleactor_aclset_adminview = invenio_explicit_acls.admin:recordroleactor_aclset_adminview',
            'systemroleactor_aclset_adminview = invenio_explicit_acls.admin:systemroleactor_aclset_adminview',
        ],
        'flask.commands': [
            'invenio_explicit_acls = invenio_explicit_acls.cli:explicit_acls'
        ],
        'invenio_celery.tasks': [
            'invenio_explicit_acls = invenio_explicit_acls.tasks'
        ],
        'invenio_db.alembic': [
            'invenio_explicit_acls = invenio_explicit_acls:alembic',
        ]
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
    ],
)
