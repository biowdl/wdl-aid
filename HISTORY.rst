.. _history:

Changelog
=========

v0.2.0-dev
----------

- Miniwdl no longer needs to be specifically version 0.5.
- The error shown when there is no workflow in the given WDL file is now
  clearer.

v0.1.1
------

- Inputs without a default will now be given a ``None`` value in the default
  field passed to jinja2, instead of a string containing ``None``.
  This should not impact generated documents (unless specific logic dealing
  with ``None`` values is used), as jinja will still render ``None`` values as
  ``None``.


v0.1.0
------

- initial release
