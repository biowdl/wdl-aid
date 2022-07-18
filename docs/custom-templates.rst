..  _custom_templates:

Custom templates
================
WDL-AID uses Jinja2_ to generate documentation files. By default a template
is provided to Jinja2 which comes packaged with WDL-AID. This default template
will result in a markdown file. If you wish to generate a differently formatted
file (eg. html) or simply want to change the content of the document then you
can provide a custom Jinja2 template. This custom template can be passed to
WDL-AID using the ``-t`` option.

.. _jinja2: https://jinja.palletsprojects.com/

The following variables are made available to the template:

- ``workflow_name``: The name of the workflow.
- ``workflow_file``: The path given as input to WDL-AID.
- ``workflow_authors``: A list of author information, taken from the
  ``authors`` field in the meta section. If this field does not contain
  a list its value will be wrapped in one.
- ``workflow_all_authors``: A list of author information taken from the
  ``authors`` fields from the workflow and called sub-workflows and tasks.
- ``workflow_meta``: A direct copy of the workflow's meta section.
- ``excluded_inputs``: A list of fully-qualified inputs which are available
  but will be excluded from the rendering process.
- ``excluded_outputs``: A list of fully-qualified ouputs which are available
  but will be excluded from the rendering process.
- ``wdl_aid_version``: The version of WDL-AID used
- ``inputs``: A dictionary which for each input category contains a list of
  dictionaries. These inner dictionaries will describe an input and
  contains the following keys:

  - ``name``: The (fully qualified) name of the input.
  - ``type``: The WDL value type of the input (eg. ``String?`` or
    ``Pair[Int, Boolean]``).
  - ``default``: The default value of the input. If an input has no
    default, then ``None``.
  - ``description``: The description of the input as specified in the
    parameter_meta sections in the WDL file(s).

- ``outputs``: A dictionary which for each output category contains a list of
  dictionaries. These inner dictionaries will describe an output and
  contains the following keys:

  - ``name``: The (fully qualified) name of the output.
  - ``type``: The WDL value type of the output (eg. ``String?`` or
    ``Pair[Int, Boolean]``).
  - ``description``: The description of the output as specified in the
    parameter_meta sections in the WDL file(s).

- ``extra``: Whatever value is contained within the JSON file
  provided though the ``-e`` option, otherwise ``None``.

Minimalistic Example
--------------------
The following is a small example of a template that could be used with
WDL-AID.

.. code-block:: html

    <html>
    <head>
        <title>{{ workflow_name }}</title>
        <style>
            ul { list-style: none; }
            li { background: #e5e5e5; padding: 10px; }
            li:nth-child(odd) { background: #f0f0f0; }
            dt { font-weight: bold }
        </style>
    </head>
    <body>
        <h1>{{ workflow_name }}</h1>
        {{ workflow_description }}
        <h2>Required Inputs</h2>

        <ul>
        {% for ri in inputs.required|sort(attribute='name') %}
            <li>
                <dl>
                    <dt>name</dt>
                    <dd>{{ ri.name }}</dd>
                    <dt>type</dt>
                    <dd>{{ ri.type }}</dd>
                    <dt>default value</dt>
                    <dd>{{ ri.default }}</dd>
                    <dt>description</dt>
                    <dd>{{ ri.description }}</dd>
                </dl>
            </li>
        {% endfor %}
        </ul>
    </body>
    </html>
