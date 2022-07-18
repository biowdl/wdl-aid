.. WDL-AID documentation master file, created by
   sphinx-quickstart on Wed Oct 23 15:49:31 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _index:

.. toctree::
   :maxdepth: 3
   :caption: Table of Contents
   :hidden:

   self
   usage
   custom-templates
   HISTORY

Welcome to WDL-AID's documentation!
===================================

Generate documentation for the inputs and outputs of WDL_ workflows,
based on the parameter_meta_ information defined in the WDL file.

WLD-AID is developed by the Sequencing Analysis Support Core at the
`Leiden University Medical Center <https://www.lumc.nl/>`_.

Quick start
-----------

Installation
^^^^^^^^^^^^

WDL-AID can be installed using:

.. code-block:: bash

   pip install wdl-aid

Basic usage
^^^^^^^^^^^
Running WDL-AID requires the following steps:

1. Add parameter_meta_ sections to you tasks and workflows.
   These should be objects containing both a description and category:

   .. code-block:: javascript

      parameter_meta {
          input_name: {
              description: "A description of what value should be provided and is what it is used for.",
              category: "required"
      }

   For inputs the available categories in the default template are:

   - ``required``
   - ``common``
   - ``advanced``
   - ``other``

   Required inputs are automatically detected and their noted category will be
   overwritten with ``required``.

   For outputs the default template will ignore the categories and simply list
   all categories under one header.

2. Once installed, WDL-AID can be run using the following command:

   .. code-block:: bash

      wdl-aid <workflow.wdl> -o docs.md

   This will generate the file ``docs.md``, containing the generated
   documentation.


Reporting bugs and feature requests
-----------------------------------
Please report any bugs, issues or pull requests on the
`github issue tracker <https://github.com/biowdl/wdl-aid/issues>`_.


Index
-----
:ref:`genindex`

.. _WDL: http://www.openwdl.org/
.. _parameter_meta: https://github.com/openwdl/wdl/blob/master/versions/1.0/SPEC.md#parameter-metadata