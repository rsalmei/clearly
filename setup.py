import os
from distutils.core import setup

from setuptools import find_packages

import clearly


def fetch_requirements(name):
    path = os.path.join('.', 'requirements', name + '.txt')
    with open(path) as f:
        return [x.strip() for x in f.readlines()]


INSTALL_REQUIRES = fetch_requirements('install')
EXTRAS_REQUIRE = {
    x: fetch_requirements(x) for x in ('test', 'dev', 'ci')
}


def get_readme():
    with open('README.md') as readme_file:
        return readme_file.read()


setup(
    name='clearly',
    version=clearly.__version__,
    description='Clearly see and debug your celery cluster in real time!',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='python celery distributed task queue flower monitor monitoring-tool asynchronous '
             'real-time realtime'.split(),
    packages=find_packages(),
    data_files=[('', ['LICENSE'])],
    python_requires='>=3.6, <4',
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        'console_scripts': [
            'clearly=clearly.command_line:clearly',
        ],
    },
)
