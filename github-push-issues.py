#!/usr/bin/env python
#
# Copyright (C) 2015 W. Trevor King <wking@tremily.us>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Create GitHub issues based on local templates.

This is useful for pushing, for example, a set of checklists with
per-item issues grouped by milestone.  The template directory
structure is::

  .
  |-- milestone-1
  |   |-- README.md
  |   |-- issue-1.1.md
  |   |-- issue-1.2.md
  |   ...
  |-- milestone-2
  |   |-- README.md
  |   |-- issue-2.1.md
  |   |-- issue-2.2.md
  |   ...
  ...

Both the ``README.md`` and per-issue files are in Markdown, with a
summary line (which may optionally include `Atx-style headers`__)
followed by a blank line and an optional Markdown body.  For example,
if you want each of your product to have a ``joel`` milestone tracking
the `Joel Test`__, you might have a ``joel/README.md`` with::

  # joel

  Keep track of how well the project handles the [Joel
  Test][joel-test].

  [joel-test]: http://www.joelonsoftware.com/articles/fog0000000043.html

And per-feature issue milestones like ``joel/source-control.md``::

  # Do you use source control?

  I've used commercial source control packages, and I've used CVS,
  which is free, and let me tell you, CVS is fine...

Of course, you probably can't copy Joel's text wholesale into your
issue files, so you'd want to make your own summaries.  Then run::

  # github-push-issues.py [options] /path/to/your/template/directory

Or::

  # github-push-issues.py [options] https://example.com/url/for/template.zip

The latter is useful if you have your template directory structure
hosted online in a version control system that supports tar or zip
archive snaphots.

__ http://daringfireball.net/projects/markdown/syntax#header
__ http://www.joelonsoftware.com/articles/fog0000000043.html
"""

import base64
import getpass
try:
    import readline
except ImportError:
    pass  # carry on without readline support
import sys
try:  # Python 2
    from urllib2 import urlopen, Request
except ImportError:  # Python 3
    from urllib.request import urlopen, Request


if sys.version_info < (3,):  # Python 2
    input = raw_input


__version__ = '0.1'


def get_authorization_headers(username=None):
    if username is None:
        username = input('GitHub username: ')
    password = getpass.getpass(prompt='GitHub password: ')
    basic_auth_payload = '{0}:{1}'.format(username, password)
    auth = 'Basic {}'.format(
        base64.b64encode(basic_auth_payload.encode('US-ASCII')))
    return {'Authorization': auth}


def add_issues(username=None):
    authorization_headers = get_authorization_headers(username=username)
    print(authorization_headers)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog='\n'.join(__doc__.splitlines()[2:]),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    parser.add_argument('-u', '--username', help='GitHub username')

    args = parser.parse_args()

    add_issues(username=args.username)
