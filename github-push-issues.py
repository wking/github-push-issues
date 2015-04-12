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
import json
import logging
import os
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
_LOG = logging.getLogger('github-push-issues')
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


class _Entry(object):
    def __init__(self, title=None, body=None):
        self.title = title
        self.body = body
        self.headers = {
            'Accept': 'application/vnd.github.full+json',
            'Content-Type': 'application/json',
        }

    def load(self, stream):
        self.title = stream.readline().strip().strip('#').strip()
        blank = stream.readline().strip()
        if blank:
            raise ValueError(
                'non-blank line after the title: {!r}'.format(blank))
        self.body = ''.join(stream.readlines())

    def create(self, root_endpoint, repository, authorization_headers):
        url = self._create_url(
            root_endpoint=root_endpoint, repository=repository)
        data = self._create_data()
        headers = authorization_headers.copy()
        headers.update(self.headers)
        request = Request(
            url=url,
            data=json.dumps(data),
            headers=headers,
            #method='POST',
        )
        _LOG.info('{method} {url}'.format(
            method=request.get_method(),
            url=request.get_full_url(),
            ))
        response = urlopen(request)
        info = response.info()
        if info.type != 'application/json':
            raise ValueError('invalid response type: {}'.format(info.type))
        payload_bytes = response.read()
        charset = info.getparam('charset')
        payload_json = payload_bytes.decode(charset)
        payload = json.loads(payload_json)
        self._create_response_json(json=payload)


class Issue(_Entry):
    def __init__(self, assignee=None, milestone=None, labels=None, **kwargs):
        super(Issue, self).__init__(**kwargs)
        self.assignee = assignee
        self.milestone = milestone
        self.labels = labels


class Milestone(_Entry):
    def __init__(self, state='open', due_on=None, **kwargs):
        super(Milestone, self).__init__(**kwargs)
        self.state = state
        self.due_on = due_on
        self.number = None

    def _create_url(self, root_endpoint, repository):
        return '{}/repos/{}/milestones'.format(
            root_endpoint.rstrip('/'), repository)

    def _create_data(self):
        data = {
            'title': self.title,
            'state': self.state,
        }
        if self.body:
            data['description'] = self.body
        if self.due_on:
            data['due_on'] = self.due_on.isoformat()
        return data

    def _create_response_json(self, json):
        self.number = json['number']


def get_authorization_headers(username=None):
    if username is None:
        username = input('GitHub username: ')
    password = getpass.getpass(prompt='GitHub password: ')
    basic_auth_payload = '{0}:{1}'.format(username, password)
    auth = 'Basic {}'.format(
        base64.b64encode(basic_auth_payload.encode('US-ASCII')))
    return {'Authorization': auth}


def add_issues(root_endpoint='https://api.github.com', username=None,
               repository=None, template_root='.'):
    authorization_headers = get_authorization_headers(username=username)
    for dirpath, dirnames, filenames in os.walk(top=template_root):
        milestone_number = None
        if 'README.md' in filenames:
            milestone = Milestone()
            with open(os.path.join(dirpath, 'README.md'), 'r') as f:
                milestone.load(stream=f)
            milestone.create(
                root_endpoint=root_endpoint,
                authorization_headers=authorization_headers,
                repository=repository)
            milestone_number = milestone.number
            filenames.remove('README.md')
        for filename in sorted(filenames):
            if not filename.endswith('.md'):
                continue
            issue = Issue(milestone=milestone_number)
            with open(os.path.join(dirpath, filename), 'r') as f:
                issue.load(stream=f)
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
    parser.add_argument(
        '--root-endpoint', default='https://api.github.com',
        help='GitHub API root endpoint')
    parser.add_argument('-u', '--username', help='GitHub username')
    parser.add_argument(
        '-r', '--repository',
        help='GitHub repository (user/repo) to push issues to')
    parser.add_argument(
        'template_root', metavar='TEMPLATE-ROOT', nargs='?', default='.',
        help='Path or URL for the template directory')

    args = parser.parse_args()

    add_issues(
        root_endpoint=args.root_endpoint,
        username=args.username,
        repository=args.repository,
        template_root=args.template_root)
