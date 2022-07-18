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
import json

import WDL
from jinja2 import Template

from wdl_aid import __version__


DEFAULT_TEMPLATE = resource_string("wdl_aid.templates",
                                   "default.md.j2").decode("utf-8")


# Helper Functions
def drop_nones(values: Dict) -> Dict:
    return {k: values[k] for k in values if values[k] is not None}


def wrap_in_list(x: Any) -> List:
    if isinstance(x, list):
        return x
    else:
        return [x]


def merge_dict_of_lists(original_dict: Dict[Any, List[Any]],
                        values_to_add: Dict[Any, List[Any]]
                        ) -> Dict[Any, List[Any]]:
    """
    Given two dictionaries of lists merge these lists into a new dictionary.
    :param original_dict: The dictionary to add items to.
    :param values_to_add: The dictionary with the items to add.
    :return: old with the new items added
    """
    for key in values_to_add:
        if key in original_dict.keys():
            for item in values_to_add[key]:
                if item not in original_dict[key]:
                    original_dict[key].append(item)
        else:
            original_dict[key] = values_to_add[key][:]
    return original_dict


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
    qualified_names = []
    for inp in inputs:
        qualified_names.append((f"{namespace}.{inp.name}", inp))
    return qualified_names


def fully_qualified_parameter_meta(parameter_meta: Dict[str, Any],
                                   namespace: str) -> Dict[str, Any]:
    """
    :param parameter_meta: A parameter_meta dictionary.
    :param namespace: The fully qualified name of the namespace.
    :return: The parameter_meta dictionary with fully qualified names
    as keys.
    """
    qualified_parameter_meta = {}
    for key in parameter_meta:
        qualified_parameter_meta[f"{namespace}.{key}"] = parameter_meta[key]
    return qualified_parameter_meta


def gather_parameter_meta(node: Union[WDL.Workflow, WDL.Conditional,
                                      WDL.Scatter],
                          namespace: str) -> Dict[str, Any]:
    """
    :param node: A node from a workflow.
    :param namespace: The node's fully qualified namespace name.
    :return: A dictionary with all the parameter meta values, using
    fully qualified namespaces as keys.
    """
    all_parameter_meta = {}
    if hasattr(node, "parameter_meta"):
        all_parameter_meta.update(fully_qualified_parameter_meta(
            node.parameter_meta, namespace))

    for element in node.body:
        if isinstance(element, WDL.Tree.Call):
            if isinstance(element.callee, WDL.Tree.Workflow):
                all_parameter_meta.update(gather_parameter_meta(
                    element.callee, f"{namespace}.{element.name}"))
            else:  # Tasks
                all_parameter_meta.update(fully_qualified_parameter_meta(
                    element.callee.parameter_meta,
                    f"{namespace}.{element.name}"))
        else:
            if isinstance(element, WDL.Tree.Conditional) or isinstance(
                    element, WDL.Tree.Scatter):
                all_parameter_meta.update(
                    gather_parameter_meta(element, namespace))
    return all_parameter_meta


def process_meta(meta: Dict[str, Any], namespace: str) -> Dict:
    """
    :param meta: The meta object to be processed.
    :param namespace: The namespace to be added to the inputs mentioned
    exclude.
    :return: A new dictionary with the exclude and authors keys.
    """
    reformatted_meta = {
        "exclude": [],
        "authors": []
    }

    wdl_aid_meta = meta.get("WDL_AID", {})
    for inp in wdl_aid_meta.get("exclude", []):
        reformatted_meta["exclude"].append(f"{namespace}.{inp}")

    reformatted_meta["authors"] = wrap_in_list(meta.get("authors", []))[:]
    return reformatted_meta


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
    collected_meta = {}
    if hasattr(node, "meta"):
        collected_meta = merge_dict_of_lists(collected_meta, process_meta(
            node.meta, namespace))
    for element in node.body:
        if isinstance(element, WDL.Tree.Call):
            if isinstance(element.callee, WDL.Tree.Workflow):
                collected_meta = merge_dict_of_lists(
                    collected_meta, gather_meta(
                        element.callee, f"{namespace}.{element.name}"))
            else:  # Tasks
                collected_meta = merge_dict_of_lists(
                    collected_meta, process_meta(
                        element.callee.meta, f"{namespace}.{element.name}"))
        else:
            if isinstance(element, WDL.Tree.Conditional) or isinstance(
                    element, WDL.Tree.Scatter):
                collected_meta = merge_dict_of_lists(
                    collected_meta, gather_meta(element, namespace))
    return collected_meta


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


def gather_inputs(workflow: WDL.Workflow
                  ) -> Tuple[List[Tuple[str, WDL.Env.Binding]], List[str]]:
    """
    :param workflow: The workflow for which the inputs are gathered.
    :return: The inputs (names, input objects) and required inputs
    (names).
    """
    inputs = fully_qualified_inputs(workflow.available_inputs, workflow.name)
    required_inputs = fully_qualified_inputs(workflow.required_inputs,
                                             workflow.name)
    required_inputs = [required_input[0] for required_input in required_inputs]
    return inputs, required_inputs


def gather_entries(name_and_bindings: List[Tuple[str, WDL.Env.Binding]],
                   parameter_meta: Dict[str, Any], category_key: str,
                   fallback_category: str, description_key: str,
                   fallback_description: str,
                   fallback_description_to_object: bool,
                   excluded_names: List[str], required_names: List[str] = []
                   ) -> Tuple[Dict[str, List[Dict[str, Any]]], List[str]]:
    """
    :param name_and_bindings: A tuple in which the first element is the
    fully qualified name of the binding in the second element.
    :param parameter_meta: A dictionary containing the parameter_meta
    information.
    :param category_key: The key used in parameter_meta for categories.
    :param fallback_category: The default category.
    :param description_key: The key used in parameter_meta for
    descriptions.
    :param fallback_description: The default description.
    :param fallback_description_to_object: Whether or not the entire
    object should be returned for a given object if the description
    key is not found.
    :param excluded_names: The names to exclude.
    :param required_names: The names to separate into a "required" category.
    :return: The entries and a list of names for which parameter_meta is
    missing.
    """
    entries = {}
    missing_parameter_meta = []
    for name, binding in name_and_bindings:
        if name in excluded_names:
            continue
        if name not in parameter_meta:
            missing_parameter_meta.append(name)
        category = ("required" if name in required_names
                    else get_category(parameter_meta, name, category_key,
                                      fallback_category))
        entry_type = (str(binding.value.type)
                      if hasattr(binding.value, "type")
                      else str(binding.value))
        entry = {
            "name": name,
            "type": entry_type,
            "description":
                get_description(parameter_meta, name, description_key,
                                fallback_description,
                                fallback_description_to_object)
        }
        if hasattr(binding.value, "expr"):
            entry["default"] = (str(binding.value.expr)
                                if binding.value.expr is not None else None)
        try:
            entries[category].append(entry)
        except KeyError:
            entries[category] = [entry]
    return entries, missing_parameter_meta


def collect_values(wdlfile: str, separate_required: bool,
                   category_key: str, fallback_category: str,
                   description_key: str, fallback_description: str,
                   fallback_description_to_object: bool,
                   strict_inputs: bool, strict_outputs: bool) -> Dict:
    """
    :param wdlfile: The workflow for which the values will be retrieved.
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
    :param strict_inputs: When true, raise a ValueError if no parameter_meta
    is available for any inputs.
    :param strict_outputs: When true, raise a ValueError if no parameter_meta
    is available for any outputs.
    :return: The values.
    """
    document = WDL.load(wdlfile)
    workflow = document.workflow
    if workflow is None:
        raise ValueError("No workflow is available in the WDL file.")

    inputs, required_inputs = gather_inputs(workflow)
    outputs = [(f"{workflow.name}.{outp.name}", outp)
               for outp in workflow.effective_outputs]
    parameter_meta = gather_parameter_meta(workflow, workflow.name)
    gathered_meta = gather_meta(workflow, workflow.name)
    authors = wrap_in_list(workflow.meta.get("authors", []))[:]

    excluded_inputs = [inp[0] for inp in inputs
                       if inp[0] in gathered_meta["exclude"]]
    excluded_outputs = [outp[0] for outp in outputs
                        if outp[0] in gathered_meta["exclude"]]

    input_entries, inputs_missing_parameter_meta = gather_entries(
        inputs, parameter_meta, category_key, fallback_category,
        description_key, fallback_description, fallback_description_to_object,
        excluded_inputs, required_inputs if separate_required else [])
    output_entries, outputs_missing_parameter_meta = gather_entries(
        outputs, parameter_meta, category_key, fallback_category,
        description_key, fallback_description, fallback_description_to_object,
        excluded_outputs)

    values = {"workflow_name": workflow.name,
              "workflow_file": wdlfile,
              "workflow_authors": authors,
              "workflow_all_authors": gathered_meta["authors"],
              "workflow_meta": workflow.meta,
              "excluded_inputs": excluded_inputs,
              "excluded_outputs": excluded_outputs,
              "inputs": input_entries,
              "outputs": output_entries,
              "wdl_aid_version": __version__}

    strict_inputs_error = (strict_inputs and
                           len(inputs_missing_parameter_meta) > 0)
    strict_outputs_error = (strict_outputs and
                            len(outputs_missing_parameter_meta) > 0)
    if strict_inputs_error or strict_outputs_error:
        error_components = []
        if strict_inputs_error:
            missed_inputs = "\n".join(inputs_missing_parameter_meta)
            error_components.append(
                f"Missing parameter_meta for inputs:\n{missed_inputs}")
        if strict_outputs_error:
            missed_outputs = "\n".join(outputs_missing_parameter_meta)
            error_components.append(
                f"Missing parameter_meta for outputs:\n{missed_outputs}")
        raise ValueError("\n\n".join(error_components))
    return values


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate documentation for a WDL workflow, based on "
                    "the parameter_meta sections.")
    parser.add_argument("-v", "--version", action="version",
                        version=f"WDL-AID {__version__}")
    parser.add_argument("wdlfile", type=str,
                        help="The WDL the documentation should be generated "
                             "for.")
    parser.add_argument("-o", "--output", type=Path,
                        help="The file to write the generated documentation "
                             "to. [stdout]")
    parser.add_argument("-t", "--template", type=Path,
                        help="A jinja2 template to use for rendering the "
                             "documentation. A default template will be "
                             "used to generate a markdown file if not "
                             "specified.")
    parser.add_argument("-c", "--category-key", type=str, default="category",
                        help="The key used in the parameter_meta sections "
                             "for the input/output category. [category]")
    parser.add_argument("-d", "--description-key", type=str,
                        default="description",
                        help="The key used in the parameter_meta section for "
                             "the input/output description. [description]")
    parser.add_argument("--do-not-separate-required", action="store_false",
                        dest="separate_required",
                        help="Do not put required inputs into a separate "
                             "'required' category, but keep them in the "
                             "category as noted in the parameter_meta "
                             "sections.")
    parser.add_argument("--fallback-description-to-object",
                        action="store_true",
                        help="Use the entire parameter_meta object as "
                             "description if the description key is not "
                             "found.")
    parser.add_argument("--fallback-description", type=str, default="???",
                        help="The fallback value for when no description is "
                             "defined for a given input/output. [???]")
    parser.add_argument("--fallback-category", type=str, default="other",
                        help="The fallback value for when no category is "
                             "defined for a given input/output. [other]")
    parser.add_argument("-e", "--extra", type=Path,
                        help="A JSON file with additional data to be passed "
                             "to the jinja2 rendering engine. These values "
                             "will be made available under the 'extra' "
                             "variable.")
    parser.add_argument("--strict", action="store_true",
                        help="Equivalent to --strict-inputs --strict outputs.")
    parser.add_argument("--strict-inputs", action="store_true",
                        help="Error if the parameter_meta entry is missing "
                             "for any inputs.")
    parser.add_argument("--strict-outputs", action="store_true",
                        help="Error if the parameter_meta entry is missing "
                             "for any outputs.")
    return parser.parse_args()


def main():
    args = parse_args()
    values = collect_values(args.wdlfile, args.separate_required,
                            args.category_key, args.fallback_category,
                            args.description_key, args.fallback_description,
                            args.fallback_description_to_object,
                            args.strict or args.strict_inputs,
                            args.strict or args.strict_outputs)
    template = Template(args.template.read_text()
                        if args.template is not None
                        else DEFAULT_TEMPLATE)

    if args.extra is not None:
        with args.extra.open("r") as extra_values_file:
            extra_values = json.load(extra_values_file)
    else:
        extra_values = None

    file_content = template.render(drop_nones(values), extra=extra_values)
    if args.output is not None:
        with args.output.open("w") as output:
            output.write(file_content)
    else:
        print(file_content, end="")


if __name__ == "__main__":
    main()
