# coding=utf-8
from __future__ import unicode_literals

from distutils.core import setup
from setuptools import find_packages

import clearly


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
        'Development Status :: 5 - Production/Stable',

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
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: 3.7',
    ],
    keywords='celery task-queue flower monitoring asynchronous'.split(),
    packages=find_packages(exclude=['img']),
    python_requires='>=2.7,<3',
    install_requires=[
        'six',
        'celery>=3.1',
        'pygments'
    ],
)
