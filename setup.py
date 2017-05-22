# coding=utf-8
from __future__ import unicode_literals

from distutils.core import setup

from setuptools import find_packages

import clearly

try:
    import pandoc
    import os

    doc = pandoc.Document()
    with open('README.md') as readme_file:
        doc.markdown = readme_file.read()
    readme = doc.rst
except:
    with open('README.md') as readme_file:
        readme = readme_file.read()

setup(
    name='clearly',
    version=clearly.__version__,
    description='Simple and accurate real-time monitor for celery',
    long_description=readme,
    url='https://github.com/rsalmei/clearly',
    author='Rogério Sampaio de Almeida',
    author_email='rsalmei@gmail.com',
    license='MIT',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Natural Language :: English',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Monitoring',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
    ],
    keywords='celery task-queue monitoring rabbitmq rabbitmq-consumer asynchronous'.split(),
    packages=find_packages(exclude=['img']),
    install_requires=[
        'six',
        'celery>=3.1,<4',
        'pygments'
    ]
)
