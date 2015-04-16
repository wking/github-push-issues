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

Both the ``README.md`` and per-issue files have a summary line (which
may optionally include `Atx-style headers`__) followed by a blank line
and an optional body.  Milestone bodies are plain text, while issue
bodies are GitHub flavored Markdown, For example, if you want each of
your product to have a ``joel`` milestone tracking the `Joel Test`__,
you might have a ``joel/README.md`` with::

  # joel

  Keep track of how well the project handles the Joel Test [1].

  [1]: http://www.joelonsoftware.com/articles/fog0000000043.html

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

Body context subsitutions
=========================

You may want to reference other issues or milestones from a given
issue or milestone body.  To fill this need, you can use `Python's
format string syntax`__ to insert information from previous issues and
milestones in a given body.  Available arguments include ``milestone``
(a dict of ``Milestone`` instances) and ``issue`` (a dict of ``Issue``
instances).  For example, you could have a body with::

  See also #{issue[joel/source-control.md].number}.

which would be expanded to::

  See also #3.

If the ``joel/source-control.md`` template had been created as issue
number 3.

__ http://daringfireball.net/projects/markdown/syntax#header
__ http://www.joelonsoftware.com/articles/fog0000000043.html
__ https://docs.python.org/3/library/string.html#format-string-syntax
"""

import base64
import codecs
import contextlib
import functools
import getpass
import io
import json
import logging
import os
try:
    import readline
except ImportError:
    pass  # carry on without readline support
import sys
import tarfile
try:  # Python 2
    from urllib2 import urlopen, Request
except ImportError:  # Python 3
    from urllib.request import urlopen, Request
import zipfile


if sys.version_info < (3,):  # Python 2
    input = raw_input


__version__ = '0.3'
_LOG = logging.getLogger('github-push-issues')
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


class _Entry(object):
    def __init__(self, title=None, body=None):
        self.title = title
        self.body = body
        self.number = None
        self.headers = {
            'Accept': 'application/vnd.github.full+json',
            'Content-Type': 'application/json; charset=UTF-8',
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
            data=json.dumps(data).encode('UTF-8'),
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

    def _create_response_json(self, json):
        self.number = json['number']
        _LOG.info('created {} #{}: {}'.format(
            type(self).__name__.lower(), self.number, self.title))


class Issue(_Entry):
    def __init__(self, assignee=None, milestone=None, labels=None, **kwargs):
        super(Issue, self).__init__(**kwargs)
        self.assignee = assignee
        self.milestone = milestone
        self.labels = labels

    def _create_url(self, root_endpoint, repository):
        return '{}/repos/{}/issues'.format(
            root_endpoint.rstrip('/'), repository)

    def _create_data(self):
        data = {
            'title': self.title,
        }
        if self.body:
            data['body'] = self.body
        if self.milestone:
            data['milestone'] = self.milestone
        if self.labels:
            data['labels'] = self.labels
        return data


class Milestone(_Entry):
    def __init__(self, state='open', due_on=None, **kwargs):
        super(Milestone, self).__init__(**kwargs)
        self.state = state
        self.due_on = due_on

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


def get_authorization_headers(username=None):
    if username is None:
        username = input('GitHub username: ')
    password = getpass.getpass(prompt='GitHub password: ')
    basic_auth_payload = '{0}:{1}'.format(username, password)
    basic_auth_bytes = base64.b64encode(basic_auth_payload.encode('US-ASCII'))
    auth = 'Basic {}'.format(basic_auth_bytes.decode('US-ASCII'))
    return {'Authorization': auth}


def walk(template_root):
    if '://' in template_root:
        base, extension = os.path.splitext(template_root)
        if extension == '.gz':
            extension = os.path.splitext(base)[1] + extension
        if extension not in ['.tar.gz', '.zip']:
            raise NotImplementedError(
                'unrecognized format for network-based template: {}'.format(
                    extension))
        response = urlopen(template_root)
        bytes = io.BytesIO(response.read())
        reader = codecs.getreader('UTF-8')
        directories = {}
        if extension == '.tar.gz':
            with tarfile.open(mode='r:*', fileobj=bytes) as f:
                def opener(member):
                    opener = contextlib.closing(reader(f.extractfile(member)))
                    opener.path = member.name
                    return opener
                for member in f.getmembers():
                    if not member.isfile():
                        continue
                    directory, filename = member.name.rsplit('/', 1)
                    if directory not in directories:
                        directories[directory] = {}
                    directories[directory][filename] = functools.partial(
                        opener, member)
                for directory, openers in sorted(directories.items()):
                    yield openers
        elif extension == '.zip':
            with zipfile.ZipFile(bytes) as f:
                def opener(name):
                    opener = reader(f.open(name, 'r'))
                    opener.path = name
                    return opener
                for name in f.namelist():
                    if name.endswith('/'):
                        continue
                    directory, filename = name.rsplit('/', 1)
                    if directory not in directories:
                        directories[directory] = {}
                    directories[directory][filename] = functools.partial(
                        opener, name)
                for directory, openers in sorted(directories.items()):
                    yield openers
    else:
        for dirpath, dirnames, filenames in os.walk(top=template_root):
            dirnames.sort()
            openers = {}
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                opener = functools.partial(open, path, 'r')
                opener.path = os.path.relpath(path, start=template_root)
                if os.path.sep != '/':
                    opener.path = opener.path.replace(os.path.sep, '/')
                openers[filename] = opener
            yield openers


def add_issues(root_endpoint='https://api.github.com', username=None,
               repository=None, template_root='.'):
    authorization_headers = get_authorization_headers(username=username)
    context = {
        'milestone': {},
        'issue': {},
    }
    for openers in walk(template_root):
        milestone_number = None
        if 'README.md' in openers:
            milestone = Milestone()
            opener = openers.pop('README.md')
            with opener() as f:
                milestone.load(stream=f)
            milestone.body = milestone.body.format(**context)
            milestone.create(
                root_endpoint=root_endpoint,
                authorization_headers=authorization_headers,
                repository=repository)
            context['milestone'][opener.path] = milestone
            milestone_number = milestone.number
        for filename, opener in sorted(openers.items()):
            if not filename.endswith('.md'):
                continue
            issue = Issue(milestone=milestone_number)
            with opener() as f:
                issue.load(stream=f)
            issue.body = issue.body.format(**context)
            issue.create(
                root_endpoint=root_endpoint,
                authorization_headers=authorization_headers,
                repository=repository)
            context['issue'][opener.path] = issue


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
