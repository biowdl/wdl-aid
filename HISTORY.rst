.. _history:

Changelog
=========

v1.0.0
------

- Strict mode can now be set for inputs and outputs separatly using the
  ``--strict-inputs`` and ``--strict-outputs`` flags respectively.
  ``--strict`` sets both to true.
- Input categories are now presented to jinja2 under the ``inputs`` variable,
  rather than as top-level variables themselves.
- The default template will now include the outputs. The outputs' categories
  are ignored by the default template.
- Documenting outputs is now supported. Information regarding the outputs
  will be presented to jinja2 under the ``outputs`` variable in a similar
  structure as the inputs, but without the ``default`` field.
- Miniwdl no longer needs to be specifically version 0.5. Version 1.0 or
  higher is now expected.
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
