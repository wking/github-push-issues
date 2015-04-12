# Copyright

"Create GitHub issues based on local templates."

import codecs as _codecs
from distutils.core import setup
import os.path as _os_path


__version__ = '0.1'
_this_dir = _os_path.dirname(__file__)


setup(
    name='github-push-issues',
    version=__version__,
    maintainer='W. Trevor King',
    maintainer_email='wking@tremily.us',
    url='https://github.com/wking/github-push-issues',
    download_url='https://github.com/wking/github-push-issues/archive/v{}.tar.gz'.format(__version__),
    license='BSD-2',
    platforms=['all'],
    description=__doc__,
    long_description=_codecs.open(
        _os_path.join(_this_dir, 'README.rst'), 'r', encoding='utf-8').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Bug Tracking',
        ],
    scripts=['github-push-issues.py'],
    provides=['github_push_issues'],
    )
