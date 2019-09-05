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
from typing import Any, Dict, List, Union, Tuple
from pkg_resources import resource_string

import WDL
from jinja2 import Template

from wdl_aid import __version__


DEFAULT_TEMPLATE = resource_string("templates",
                                   "default.md.j2").decode("utf-8")


# Helper Functions
def drop_nones(values: Dict) -> Dict:
    return {k: values[k] for k in values if values[k] is not None}


def wrap_in_list(x: Any) -> List:
    if isinstance(x, list):
        return x
    else:
        return [x]


def merge_dict_of_lists(old: Dict[Any, List[Any]],
                        new: Dict[Any, List[Any]]) -> Dict[Any, List[Any]]:
    """
    Given two dictionaries of lists merge these lists into a new dictionary.
    :param old: The dictionary to add items to.
    :param new: The dictionary with the items to add.
    :return: old with the new items added
    """
    for key in new:
        if key in old.keys():
            for item in new[key]:
                if item not in old[key]:
                    old[key].append(item)
        else:
            old[key] = new[key][:]
    return old


# Data gathering functions
def fully_qualified_inputs(inputs: WDL.Env.Bindings,
                           namespace: str) -> List[Tuple[str,
                                                         WDL.Env.Binding]]:
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
                          namespace: str) -> Dict[str, Any]:
    """
    :param node: A node from a workflow.
    :param namespace: The node's fully qualified namespace name.
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


def process_meta(meta: Dict[str, Any], namespace: str) -> Dict:
    """
    :param meta: The meta object to be processed.
    :param namespace: The namespace to be added to the inputs mentioned
    exclude.
    :return: A new dictionary with the exclude and authors keys.
    """
    out = {
        "exclude": [],
        "authors": []
    }
    wdl_aid_meta = meta.get("WDL_AID", {})
    for inp in wdl_aid_meta.get("exclude", []):
        out["exclude"].append("{}.{}".format(namespace, inp))
    out["authors"] = wrap_in_list(meta.get("authors", []))[:]
    return out


def gather_meta(node: Union[WDL.Workflow, WDL.Conditional,
                            WDL.Scatter], namespace: str) -> Dict[str, Any]:
    """
    :param node: A node from a workflow.
    :param namespace: The node's fully qualified namespace name.
    :return: A dictionary with the WDL_AID recognized meta values:
        - "exclude": A list of inputs to be excluded.
        - "authors": A list of all authors mentioned in any called
          workflow or task.
    """
    out = {}
    if hasattr(node, "meta"):
        out = merge_dict_of_lists(out, process_meta(node.meta, namespace))
    for el in node.body:
        if hasattr(el, "callee"):  # Calls
            if hasattr(el.callee, "body"):  # sub-workflow
                out = merge_dict_of_lists(out, gather_meta(el.callee,
                    "{}.{}".format(namespace, el.name)))
            else:  # Tasks
                out = merge_dict_of_lists(out, process_meta(el.callee.meta,
                    "{}.{}".format(namespace, el.name)))
        else:
            if hasattr(el, "body"):  # if or scatter
                out = merge_dict_of_lists(out, gather_meta(el, namespace))
    return out


def get_description(parameter_meta: dict, input_name: str,
                    description_key: str = "description",
                    fallback_description: str = "???",
                    fallback_description_to_object: bool = False) -> str:
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
                 fallback_category: str = "other") -> str:
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


def gather_inputs(wf: WDL.Workflow) -> Tuple[List[Tuple[str, WDL.Env.Binding]],
                                             List[str]]:
    """
    :param wf: The workflow for which the inputs are gathered.
    :return: The inputs (names, input objects) and required inputs
    (names).
    """
    inputs = fully_qualified_inputs(wf.available_inputs, wf.name)
    required_inputs = fully_qualified_inputs(wf.required_inputs, wf.name)
    required_inputs = [required_input[0] for required_input in required_inputs]
    return inputs, required_inputs


def collect_values(wf: WDL.Workflow, separate_required: bool,
                   category_key: str, fallback_category: str,
                   description_key: str, fallback_description: str,
                   fallback_description_to_object: bool) -> Dict:
    """
    :param wf: The workflow for which the values will be retrieved.
    :param separate_required: Whether or not to put required inputs in a
    separate category.
    :param category_key: The key used in parameter_meta for categories.
    :param fallback_category: The default category.
    :param description_key: The key used in parameter_meta for
    descriptions.
    :param fallback_description: The default description.
    :param fallback_description_to_object: Whether or not the entire
    object should be returned for a given object if the description
    key is not found.
    :return: The values.
    """
    inputs, required_inputs = gather_inputs(wf)
    parameter_meta = gather_parameter_meta(wf, wf.name)
    meta = gather_meta(wf, wf.name)
    authors = wrap_in_list(wf.meta.get("authors", []))[:]
    values = {"workflow_name": wf.name,
              "workflow_description": wf.meta.get("description", None),
              "workflow_authors": authors,
              "workflow_all_authors": meta["authors"],
              "workflow_author": wf.meta.get("author", None),
              "workflow_email": wf.meta.get("email", None),
              "excluded_inputs": meta["exclude"],
              "wdl_aid_version": __version__}
    for name, inp in inputs:
        if name in meta["exclude"]:
            continue
        category = ("required"
                    if name in required_inputs and separate_required
                    else get_category(parameter_meta, name, category_key,
                                      fallback_category))
        entry = {
            "name": name,
            "type": str(inp.value.type),
            "default": str(inp.value.expr),
            "description":
                get_description(parameter_meta, name, description_key,
                                fallback_description,
                                fallback_description_to_object)
        }
        try:
            values[category].append(entry)
        except KeyError:
            values[category] = [entry]
    return values


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
    parser.add_argument("--do-not-separate-required", action="store_false",
                        dest="separate_required",
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
    values = collect_values(wf, args.separate_required, args.category_key,
                            args.fallback_category, args.description_key,
                            args.fallback_description,
                            args.fallback_description_to_object)
    template = Template(args.template.read_text()
                        if args.template is not None
                        else DEFAULT_TEMPLATE)
    file_content = template.render(drop_nones(values))
    if args.output is not None:
        with args.output.open("w") as output:
            output.write(file_content)
    else:
        print(file_content, end="")


if __name__ == "__main__":
    main()
