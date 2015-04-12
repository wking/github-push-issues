Create GitHub issues based on local templates.

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

__ http://daringfireball.net/projects/markdown/syntax#header
__ http://www.joelonsoftware.com/articles/fog0000000043.html

