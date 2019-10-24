# WDL-AID
Generate documentation for the inputs of WDL workflows, based on the
parameter_meta information defined in the WDL file.

## usage
```
usage: wdl-aid [-h] [-v] [-o OUTPUT] [-t TEMPLATE] [-c CATEGORY_KEY]
               [-d DESCRIPTION_KEY] [--do-not-separate-required]
               [--fallback-description-to-object]
               [--fallback-description FALLBACK_DESCRIPTION]
               [--fallback-category FALLBACK_CATEGORY] [-e EXTRA] [--strict]
               wdlfile

Generate documentation for a WDL workflow, based on the parameter_meta
sections.

positional arguments:
  wdlfile               The WDL the documentation should be generated for.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -o OUTPUT, --output OUTPUT
                        The file to write the generated documentation to.
  -t TEMPLATE, --template TEMPLATE
                        A jinja2 template to use for rendering the
                        documentation. A default template will be used to
                        generate a markdown file if not specified.
  -c CATEGORY_KEY, --category-key CATEGORY_KEY
                        The key used in the parameter_meta sections for the
                        input category. [category]
  -d DESCRIPTION_KEY, --description-key DESCRIPTION_KEY
                        The key used in the parameter_meta section for the
                        input description. [description]
  --do-not-separate-required
                        Do not put required inputs into a separate 'required'
                        category, but keep them in the category as noted in
                        the parameter_meta sections.
  --fallback-description-to-object
                        Use the entire parameter_meta object as description if
                        the description key is not found.
  --fallback-description FALLBACK_DESCRIPTION
                        The fallback value for when no description is defined
                        for a given input. [???]
  --fallback-category FALLBACK_CATEGORY
                        The fallback value for when no category is defined for
                        a given input. [other]
  -e EXTRA, --extra EXTRA
                        A JSON file with additional data to be passed to the
                        jinja2 rendering engine. These values will be made
                        available under the 'extra' variable.
  --strict              Error if the parameter_meta entry is missing for any
                        inputs.
```

## Preparing your WDL file
Your WDL file should include the parameter_meta section. WDL-AID will
retrieve the descriptions and categories for the inputs from these
sections. By default the parameter_meta items are expected to be
objects containing a `description` and a `category` field.
For example:
```wdl
parameter_meta {
    message: {
       description: "Some text"
       category: "required" 
    }
    output_file: {
        description: "A file to write the message to"
        category: "common"
    }
}
```
> Note that WDL-AID will, by default, separate the required inputs from
the rest and assign them the `required` category regardless of the
category assigned in the parameter_meta section.

### Excluding inputs
Inputs can be excluded by noting them in the `meta` section of a 
workflow or task. Inside the meta section a list named `exclude` should
be added inside a `WDL_AID` object. They have to be noted relative 
to the workflow or task the meta section is defined in.
For example:
```wdl
meta {
    WDL_AID: {
        exclude: ["workflow_input", "some_call.task_input"]
    }
}
``` 

## The default template
The default template will render a markdown file only describing the
inputs. You will likely want to write a template with some additional
information about the workflow in question.

The default template contains supports the following categories:
- required
- common
- advanced
- other

The default template contains support for the following meta fields:
- description
- authors: This is expected to be an object containing the following
  fields for each author:
  - name
  - email (optional)
  - organization (optional)

## Custom templates
A custom template can be provided using the `-t` option. This should be
a Jinja2 template.
The following variables are made available to the template:
- `workflow_name`: The name of the workflow.
- `workflow_file`: The path given as input to WDL-AID.
- `workflow_authors`: A list of author information, taken from the
  `authors` field in the meta section. If this field does not contain
  a list its value will be wrapped in one.
- `workflow_all_authors`: A list of author information taken from the
  `authors` fields from the workflow and called sub-workflows and tasks.
- `workflow_meta`: A direct copy of the workflow's meta section.
- `excluded_inputs`: A list of fully-qualified inputs which will be
  excluded from the rendering process (see
  [Excluding inputs](#excluding-inputs)).
- `wdl_aid_version`: The version of WDL-AID used
- Per category a list of dictionaries. Each of these dictionaries will
  describe an input and contains the following keys:
  - `name`: The (fully qualified) name of the input.
  - `type`: The WDL value type of the input (eg. `String?` or 
    `Pair[Int, Boolean]`).
  - `default`: The default value of the input. If an input has no
    default, then `None`.
  - `description`: The description of the input as specified in the
    parameter_meta sections in the WDL file(s).
- `extra`: Whatever value is contained within the JSON file
  provided though the `-e` option, otherwise `None`.
