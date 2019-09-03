# Copyright (c) 2019 Leiden University Medical Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Union

import WDL
from jinja2 import Template

from wdl_aid import __version__


DEFAULT_TEMPLATE = dedent("""
    # {{ workflow_name }}: Inputs
    The following are all available inputs for `{{workflow_name}}`.

    {% if required is defined %}
    ## Required inputs
    {% for ri in required -%}
    <p name="{{ ri.name }}">
        <b>{{ ri.name }}</b><br />
        <i>{{ ri.type }} &mdash; Default: {{ ri.default }}</i><br />
        {{ ri.description }}
    </p>
    {% endfor -%}
    {% endif -%}

    {% if common is defined %}
    ## Other common inputs
    {% for ci in common -%}
    <p name="{{ ci.name }}">
        <b>{{ ci.name }}</b><br />
        <i>{{ ci.type }} &mdash; Default: {{ ci.default }}</i><br />
        {{ ci.description }}
    </p>
    {% endfor -%}
    {% endif -%}

    {% if advanced is defined %}
    ## Advanced inputs
    <details>
    <summary> Show/Hide </summary>
    {% for ai in advanced -%}
    <p name="{{ ai.name }}">
        <b>{{ ai.name }}</b><br />
        <i>{{ ai.type }} &mdash; Default: {{ ai.default }}</i><br />
        {{ ai.description }}
    </p>
    {% endfor -%}
    {% endif -%}

    {% if other is defined %}
    ## Other inputs
    <details>
    <summary> Show/Hide </summary>
    {% for oi in other -%}
    <p name="{{ oi.name }}">
        <b>{{ oi.name }}</b><br />
        <i>{{ oi.type }} &mdash; Default: {{ oi.default }}</i><br />
        {{ oi.description }}
    </p>
    {% endfor -%}
    {% endif -%}

    </details>

    > Generated using WDL AID ({{ wdl_aid_version }})

    """)


def fully_qualified_inputs(inputs: WDL.Env.Bindings,
                           namespace: str) -> (str, WDL.Decl):
    """
    :param inputs: A list of Bindings from a Namespace.
    :param namespace: The fully qualified name of the namespace.
    :return: A list of tuples containing the fully qualified input name
    and the input Decl.
    """
    out = []
    for inp in inputs:
        out.append(("{}.{}".format(namespace, inp.name), inp))
    return out


def fully_qualified_parameter_meta(parameter_meta: Dict[str, Any],
                                   namespace: str) -> Dict[str, Any]:
    """
    :param parameter_meta: A parameter_meta dictionary.
    :param namespace: The fully qualified name of the namespace.
    :return: The parameter_meta dictionary with fully qualified names
    as keys.
    """
    out = {}
    for key in parameter_meta:
        out["{}.{}".format(namespace, key)] = parameter_meta[key]
    return out


def gather_parameter_meta(node: Union[WDL.Workflow, WDL.Conditional,
                                      WDL.Scatter],
                          namespace: str,
                          ) -> Dict[str, Any]:
    """
    :param node: A node from a workflow.
    :param namespace: The nodes fully qualified namespace name.
    :return: A dictionary with all the parameter meta values, using
    fully qualified namespaces as keys.
    """
    out = {}
    if hasattr(node, "parameter_meta"):
        out.update(fully_qualified_parameter_meta(node.parameter_meta,
                                                  namespace))

    for el in node.body:
        if hasattr(el, "callee"):  # Calls
            if hasattr(el.callee, "body"):  # sub-workflow
                out.update(gather_parameter_meta(el.callee, "{}.{}".format(
                    namespace, el.name)))
            else:  # Tasks
                out.update(
                    fully_qualified_parameter_meta(el.callee.parameter_meta,
                                                   "{}.{}".format(namespace,
                                                                  el.name)))
        else:
            if hasattr(el, "body"):  # if or scatter
                out.update(gather_parameter_meta(el, namespace))
    return out


def get_description(parameter_meta: dict, input_name: str,
                    description_key: str = "description",
                    fallback_description: str = "???",
                    fallback_description_to_object: bool = False):
    """
    :param parameter_meta: A dictionary containing the parameter_meta
    information.
    :param input_name: The name of the input for which the description
    should be retrieved (the key in the parameter_meta dictionary).
    :param description_key: If the parameter_meta[input_name] is a dict,
    the key which contains the descriptions.
    :param fallback_description: A description to return of no
    description is found.
    :param fallback_description_to_object: Whether ot not to return the
    entire parameter_meta[input_name] object, if no description is
    found.
    :return: The description of the input.
    """
    try:
        entry = parameter_meta.get(input_name, None)
        return entry.get(description_key,
                         entry
                         if fallback_description_to_object
                         else fallback_description)
    except AttributeError:  # The parameter_meta for this input is not a dict.
        if fallback_description_to_object:
            return parameter_meta.get(input_name, fallback_description)
        else:
            return fallback_description


def get_category(parameter_meta: Any, input_name: str,
                 category_key: str = "category",
                 fallback_category: str = "other"):
    """
    :param parameter_meta: A dictionary containing the parameter_meta
    information.
    :param input_name: The name of the input for which the category
    should be retrieved (the key in the parameter_meta dictionary).
    :param category_key: If the parameter_meta[input_name] is a dict,
    the key which contains the category.
    :param fallback_category: A category to return of no
    description is found.
    :return: The category of the input.
    """
    try:
        return parameter_meta.get(input_name, {}).get(category_key,
                                                      fallback_category)
    except AttributeError:
        return fallback_category


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate documentation for a WDL workflow, based on "
                    "the parameter_meta sections.")
    parser.add_argument("wdlfile", type=str,
                        help="The WDL the documentation should be generated "
                             "for.")
    parser.add_argument("-o", "--output", type=Path,
                        help="The file to write the generated documentation "
                             "to.")
    parser.add_argument("-t", "--template", type=Path,
                        help="A jinja2 template to use for rendering the "
                             "documentation. A default template will be "
                             "used to generate a markdown file if not "
                             "specified.")
    parser.add_argument("-c", "--category-key", type=str, default="category",
                        help="The key used in the parameter_meta sections "
                             "for the input category. [category]")
    parser.add_argument("-d", "--description-key", type=str,
                        default="description",
                        help="The key used in the parameter_meta section for "
                             "the input description. [description]")
    parser.add_argument("--do-not-separate-required", action="store_true",
                        help="Do not put required inputs into a separate "
                             "'required' category, but keep them in the. "
                             "category as noted in the parameter_meta "
                             "sections.")
    parser.add_argument("--fallback-description-to-object",
                        action="store_true",
                        help="Use the entire parameter_meta object as "
                             "description if the description key is not "
                             "found.")
    parser.add_argument("--fallback-description", type=str, default="???",
                        help="The fallback value for when no description is "
                             "defined for a given input. [???]")
    parser.add_argument("--fallback-category", type=str, default="other",
                        help="The fallback value for when no category is "
                             "defined for a given input. [other]")
    return parser.parse_args()


def main():
    args = parse_args()
    doc = WDL.load(args.wdlfile)

    wf = doc.workflow
    inputs = fully_qualified_inputs(wf.available_inputs, wf.name)
    inputs = sorted(inputs, key=lambda i: i[0])

    if args.do_not_separate_required:
        required_inputs = []
    else:
        required_inputs = fully_qualified_inputs(wf.required_inputs, wf.name)
        required_inputs = [required_input[0]
                           for required_input in required_inputs]

    parameter_meta = gather_parameter_meta(wf, wf.name)

    values = {"workflow_name": wf.name, "wdl_aid_version": __version__}

    for name, inp in inputs:
        category = ("required"
                    if name in required_inputs
                    else get_category(parameter_meta, name,
                                      args.category_key,
                                      args.fallback_category))
        entry = {
            "name": name,
            "type": inp.value.type,
            "default": str(inp.value.expr),
            "description":
                get_description(parameter_meta, name, args.description_key,
                                args.fallback_description,
                                args.fallback_description_to_object)
            }
        try:
            values[category].append(entry)
        except KeyError:
            values[category] = [entry]

    template = Template(args.template.read_text()
                        if args.template is not None
                        else DEFAULT_TEMPLATE)
    file_content = template.render(values)

    if args.output is not None:
        with args.output.open("w") as output:
            output.write(file_content)
    else:
        print(file_content, end="")


if __name__ == "__main__":
    main()
