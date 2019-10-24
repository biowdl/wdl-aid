.. _usage:

Usage
=====
Preparing your WDL files
------------------------
Before the documentation can be generated, each input in your WDL_ file must
be given a description and category. This is done using WDL's parameter_meta_
section:

.. code-block::

    parameter_meta {
        name_of_input: {
            description: "Some description of the input",
            category: "some category"
        }
    }

These fields (``description`` and ``category`` may also be called differently,
but you will have to set some additional options when running WDL-AID, see
`Custom description and category keys`_.

WDL-AID will separate the inputs by category, so each category may be rendered
in its own section. Required inputs are automatically detected and assigned
the ``required`` category, overwriting the one noted in the parameter_meta
section.

The default template supports the following categories:

- ``required``
- ``common``
- ``advanced``
- ``other``

Excluding inputs
^^^^^^^^^^^^^^^^
In some cases there may be inputs which should not be included in the
documentation, eg. when using a sub-workflow which provides options which make
no sense in the context of the overarching workflow. You can tell WDL_AID to
omit certain inputs by adding the following to your workflow's meta_ section:

.. code-block::

    WDL_AID: {
        exclude: ["input_name", "call.input_name"]
    }

The inputs added here may be of the workflow or task containing the meta section
or from any call made inside of the workflow. Be sure to use the input_names
qualified relative to this workflow, ie. ``input_name`` for inputs of the
task/workflow itself, ``call_name.input_name`` for inputs of calls,
``call_name.sub_call_name.input_name`` for calls inside of sub-workflows, etc.

Metadata
^^^^^^^^
The meta_ section of your workflow may also be used to pass additional
information along to WDL-AID. The entire meta section of the workflow
that WDL-AID gets called on is passed to the template unaltered.
WDL-AID will also retrieve all authors from the meta sections of every called
task and workflow and pass these along.

The default template supports the following meta section entries:

- ``description`` (only for the root workflow)
- ``authors`` (also for sub-workflows and tasks)

    This is expected to be an object containing the following
    fields for each author:

    - ``name``
    - ``email`` (optional)
    - ``organization`` (optional)

    eg.

    .. code-block::

        meta {
            authors: [
                {
                    name: "Eddard Stark",
                    email: "StarkNed@winterfell.westeros",
                    organization: "The North"
                },{
                    name: "Jon Snow",
                    email: "j.snow@nightswatch.westeros",
                    organization: "The Night's Watch"
                }
            ]
        }

Running WDL-AID
---------------

.. program:: wdl-aid

WDL-AID can be run with the following command:

.. code-block::

    wdl-aid <workflow.wdl>

This will print the generated documentation to ``stdout``. This will be
markdown formatted text when using the default template.

Writing to a file
^^^^^^^^^^^^^^^^^
To write the output to a file the following option can be used:

.. option:: -o OUTPUT, --output OUTPUT

    The file to write the generated documentation to.

Fallback/default values
^^^^^^^^^^^^^^^^^^^^^^^
If no description or category is defined then WDL-AID will fallback to a default
value. By default these values equal ``???`` and ``other`` respectively.
You may override these fallback values using the following options:

.. option:: --fallback-description FALLBACK_DESCRIPTION

    The fallback value for when no description is defined for a given input.

.. option:: --fallback-category FALLBACK_CATEGORY

    The fallback value for when no category is defined for a given input.

In some cases a parameter_meta_ entry may be defined, but it does not contain the
an object with a description item. By default the fallback values will get used
in these cases. However, alternatively you can use the entirety of the defined
parameter_meta entry as description value using the following flag:

.. option:: --fallback-description-to-object

    Use the entire parameter_meta object as description if the description key is not found.

Custom description and category keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In case your parameter_meta_ entries use different keys than ``description``
and ``category`` to provide the description and category (respectively) of the
inputs, you can use the following options to inform WDL-AID of which keys to
look for:

.. option:: -c CATEGORY_KEY, --category-key CATEGORY_KEY

    The key used in the parameter_meta sections for the input category.

.. option:: -d DESCRIPTION_KEY, --description-key DESCRIPTION_KEY

    The key used in the parameter_meta section for the input description.

Keeping original categories for required inputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you wish to retain the categories noted in the parameter_meta_ sections for
the required input, rather then having the overwritten with ``required`` then
you can use the following flag:

.. option::--do-not-separate-required

    Do not put required inputs into a separate 'required'  category, but
    keep them in the category as noted in the parameter_meta sections.

Custom templates
^^^^^^^^^^^^^^^^
You can provide a custom template using the following option. This template
should be a Jinja2_ template.

.. option:: -t TEMPLATE, --template TEMPLATE

    A Jinja2 template to use for rendering the documentation.

See :ref:`custom_templates` for more details on making a custom template.

Extra data
^^^^^^^^^^
It is possible to pass extra data along to the template. This can be done by
providing the following option with a json file which contains this extra data.

.. option:: -e EXTRA, --extra EXTRA

    A JSON file with additional data to be passed to the jinja2 rendering engine.

Strict mode
^^^^^^^^^^^
WDL-AID has an option to run in a "strict" mode. This entails that WDL-AID will
error if any inputs are missing a parameter_meta section. This may be useful
as part of CI testing, allowing you to ensure that all inputs will always be
documented.

.. option:: --strict

  Error if the parameter_meta entry is missing for any inputs.

.. _WDL: http://www.openwdl.org/
.. _parameter_meta: https://github.com/openwdl/wdl/blob/master/versions/1.0/SPEC.md#parameter-metadata
.. _meta: https://github.com/openwdl/wdl/blob/master/versions/1.0/SPEC.md#metadata
.. _jinja2: https://jinja.palletsprojects.com/