# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

import sys
from distutils.core import setup

from setuptools import find_packages

import clearly

install_requires = [
    'six',
    'celery>=3.1',
    'pygments',
    'grpcio',
    'protobuf',
    'click',
    'about-time',
]
if sys.version_info[0] == 2:
    install_requires.append('futures')


def get_readme():
    with open('README.md') as readme_file:
        return readme_file.read()


setup(
    name='clearly',
    version=clearly.__version__,
    description='Simple and accurate real-time monitor for celery',
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/rsalmei/clearly',
    author=clearly.__author__,
    author_email=clearly.__email__,
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
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Monitoring',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='celery task queue job flower monitoring distributed asynchronous'.split(),
    packages=find_packages(),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4, <4',
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'clearly=clearly.command_line:clearly',
        ],
    },
)
