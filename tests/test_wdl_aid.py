# Copyright (c) 2019 Leiden University Medical Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
from pathlib import Path

import pytest
import WDL

import wdl_aid.wdl_aid as wa

filesdir = Path(__file__).parent / Path("files")


def test_drop_nones():
    assert wa.drop_nones({1: 1, 2: 2, 3: None}) == {1: 1, 2: 2}


def test_wrap_in_list():
    assert wa.wrap_in_list(1) == [1]
    assert wa.wrap_in_list([1]) == [1]


def test_merge_dict_of_lists():
    assert wa.merge_dict_of_lists(
        {1: [1, 2], 2: [1,2]},
        {1: [2, 3], 3: [1]}) == {1: [1, 2, 3], 2: [1, 2], 3: [1]}


def test_fully_qualified_inputs():
    doc = WDL.load(str(filesdir / Path("workflow.wdl")))
    available_inputs = doc.workflow.available_inputs
    qualified_names = wa.fully_qualified_inputs(available_inputs,
                                                doc.workflow.name)
    assert {x[0] for x in qualified_names} == {"test.sw.workflowOptional",
                                               "test.echo.shouldBeExcluded",
                                               "test.echo.missingDescription",
                                               "test.echo.taskOptional",
                                               "test.input2", "test.input1"}


def test_fully_qualified_parameter_meta():
    test_dict = {"bots": "zeven dagen lang", "eluveitie": "lvgvs"}
    result = wa.fully_qualified_parameter_meta(test_dict, "Son_ar_chistr")
    assert result == {"Son_ar_chistr.bots": "zeven dagen lang",
                      "Son_ar_chistr.eluveitie": "lvgvs"}


def test_gather_parameter_meta():
    doc = WDL.load(str(filesdir / Path("workflow.wdl")))
    parameter_meta = wa.gather_parameter_meta(doc.workflow, doc.workflow.name)
    assert parameter_meta == {"test.input1": "The first input",
                              "test.input2": "The second input",
                              "test.echo.taskOptional":
                                  {"description": "an optional input",
                                   "category": "advanced",
                                   "desc": "alternative description",
                                   "cat": "common"},
                              "test.output1": "It does but it is blatantly obvious and simplistic.",
                              "test.output3": {"description": "A very descriptive description."},
                              "test.output4": {"description": "This one has a category!", 
                                               "category": "category"}
                              }


def test_process_meta():
    meta = {"WDL_AID": {"exclude": ["A", "B"]},
            "authors": ["A", "B"]}
    assert wa.process_meta(meta, "trinket") == {
        "exclude": ["trinket.A", "trinket.B"],
        "authors": ["A", "B"]
    }
    meta2 = {"WDL_AID": {"exclude": ["A", "B"]},
             "authors": "me! :3"}
    assert wa.process_meta(meta2, "trinket") == {
        "exclude": ["trinket.A", "trinket.B"],
        "authors": ["me! :3"]
    }


def test_gather_meta():
    doc = WDL.load(str(filesdir / Path("workflow.wdl")))
    meta = wa.gather_meta(doc.workflow, doc.workflow.name)
    assert meta == {
        "exclude": ["test.echo.shouldBeExcluded", "test.output5"],
        "authors": [{
            "name": "Percy",
            "email": "PercivalFredrickSteinVonMuselKlossowskiDeRolothe3rd@whitestone.net",
            "organization": "Vox Machina"
        }, {
            "name": "'Caleb'",
            "email": "c.widowghast@example.com",
            "organization": "The Mighty Nein"
        }]
    }


def test_get_description_defaults():
    a_dict = {"Vax": {"description": "A half-elf rogue"},
              "Vex": {"desc": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_description(a_dict, "Vax") == "A half-elf rogue"
    assert wa.get_description(a_dict, "Vex") == "???"
    assert wa.get_description(a_dict, "Keyleth") == "???"
    assert wa.get_description(a_dict, "Grog") == "???"


def test_get_description_description_key():
    a_dict = {"Vax": {"description": "A half-elf rogue"},
              "Vex": {"desc": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_description(a_dict, "Vax", description_key="desc") == "???"
    assert wa.get_description(a_dict, "Vex", description_key="desc") == "A half-elf ranger"
    assert wa.get_description(a_dict, "Keyleth", description_key="desc") == "???"
    assert wa.get_description(a_dict, "Grog", description_key="desc") == "???"


def test_get_description_fallback_description():
    a_dict = {"Vax": {"description": "A half-elf rogue"},
              "Vex": {"desc": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_description(a_dict, "Vax", fallback_description="A VM member") == "A half-elf rogue"
    assert wa.get_description(a_dict, "Vex", fallback_description="A VM member") == "A VM member"
    assert wa.get_description(a_dict, "Keyleth", fallback_description="A VM member") == "A VM member"
    assert wa.get_description(a_dict, "Grog", fallback_description="A VM member") == "A VM member"


def test_get_description_fallback_description_to_object():
    a_dict = {"Vax": {"description": "A half-elf rogue"},
              "Vex": {"desc": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_description(a_dict, "Vax", fallback_description_to_object=True) == "A half-elf rogue"
    assert wa.get_description(a_dict, "Vex", fallback_description_to_object=True) == {"desc": "A half-elf ranger"}
    assert wa.get_description(a_dict, "Keyleth", fallback_description_to_object=True) == "A half-elf druid"
    assert wa.get_description(a_dict, "Grog", fallback_description_to_object=True) == "???"


def test_get_category_defaults():
    a_dict = {"Vax": {"category": "A half-elf rogue"},
              "Vex": {"cat": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_category(a_dict, "Vax") == "A half-elf rogue"
    assert wa.get_category(a_dict, "Vex") == "other"
    assert wa.get_category(a_dict, "Keyleth") == "other"
    assert wa.get_category(a_dict, "Grog") == "other"


def test_get_category_category_key():
    a_dict = {"Vax": {"category": "A half-elf rogue"},
              "Vex": {"cat": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_category(a_dict, "Vax", category_key="cat") == "other"
    assert wa.get_category(a_dict, "Vex", category_key="cat") == "A half-elf ranger"
    assert wa.get_category(a_dict, "Keyleth", category_key="cat") == "other"
    assert wa.get_category(a_dict, "Grog", category_key="cat") == "other"


def test_get_category_fallback_category():
    a_dict = {"Vax": {"category": "A half-elf rogue"},
              "Vex": {"cat": "A half-elf ranger"},
              "Keyleth": "A half-elf druid"}
    assert wa.get_category(a_dict, "Vax", fallback_category="VM member") == "A half-elf rogue"
    assert wa.get_category(a_dict, "Vex", fallback_category="VM member") == "VM member"
    assert wa.get_category(a_dict, "Keyleth", fallback_category="VM member") == "VM member"
    assert wa.get_category(a_dict, "Grog", fallback_category="VM member") == "VM member"


def test_gather_inputs():
    doc = WDL.load(str(filesdir / Path("workflow.wdl")))
    inputs, required_inputs = wa.gather_inputs(doc.workflow)
    assert required_inputs == ["test.input1"]
    for name, binding in inputs:
        assert name in ["test.sw.workflowOptional",
                        "test.echo.shouldBeExcluded",
                        "test.echo.missingDescription",
                        "test.echo.taskOptional",
                        "test.input2",
                        "test.input1"]
        assert isinstance(binding, WDL.Env.Binding)


def test_collect_values():
    values = wa.collect_values(str(filesdir / Path("workflow.wdl")), True,
                               "category", "other", "description", "...",
                               False, False, False)
    assert isinstance(values, dict)
    assert values["workflow_name"] == "test"
    assert values["workflow_file"] == str(filesdir / Path("workflow.wdl"))
    assert values["workflow_authors"] ==  [{
        "name": "Percy",
        "email": "PercivalFredrickSteinVonMuselKlossowskiDeRolothe3rd@whitestone.net",
        "organization": "Vox Machina"
    }]
    assert values["workflow_all_authors"] == [{
        "name": "Percy",
        "email": "PercivalFredrickSteinVonMuselKlossowskiDeRolothe3rd@whitestone.net",
        "organization": "Vox Machina"
    }, {
        "name": "'Caleb'",
        "email": "c.widowghast@example.com",
        "organization": "The Mighty Nein"
    }]
    assert values["workflow_meta"] == {
        "WDL_AID": {
            "exclude": ["echo.shouldBeExcluded", "output5"]
        },
        "authors": {
            "name": "Percy",
            "email": "PercivalFredrickSteinVonMuselKlossowskiDeRolothe3rd@whitestone.net",
            "organization": "Vox Machina"
        },
        "author": "Whomever",
        "email": "whatever@where-ever.meh",
        "description": "Once upon a midnight dreary, while I pondered, weak and weary, over many a quant and curious volumne of forgotten lore. While I nodded, nearly napping, suddenly there came a tapping, as if some one gently rapping, rapping at my chamber door. \"'Tis some visitor,\" I muttered, \"Tapping at my chamber door. This it is and nothing more!\""
    }
    assert values["excluded_inputs"] == ["test.echo.shouldBeExcluded"]
    assert values["excluded_outputs"] == ["test.output5"]
    assert values["wdl_aid_version"] == wa.__version__
    assert all(
        [entry in [
            {
                "default": None,
                "description": "...",
                "name": "test.sw.workflowOptional",
                "type": "String?"
            }, {
                "default": None,
                "description": "...",
                "name": "test.echo.missingDescription",
                "type": "String?"
            }, {
                "default": '":p"',
                "description": "...",
                "name": "test.input2",
                "type": "String"
            }
        ] for entry in values["inputs"]["other"]])
    assert values["inputs"]["required"] == [{
        "default": None,
        "description": "...",
        "name": "test.input1",
        "type": "String"
    }]
    assert values["inputs"]["advanced"] == [{
        "default": None,
        "description": "an optional input",
        "name": "test.echo.taskOptional",
        "type": "String?"
    }]
    assert values["outputs"]["other"] == [
        {
            "description": "...",
            "name": "test.output1",
            "type": "String?"
        },{
            "description": "...",
            "name": "test.output2",
            "type": "String"
        },{
            "description": "A very descriptive description.",
            "name": "test.output3",
            "type": "Array[File]"
        }
    ]
    assert values["outputs"]["category"] == [{
        "description": "This one has a category!",
        "name": "test.output4",
        "type": "Int"
    }]


def test_collect_values_strict():
    with pytest.raises(ValueError):
        values = wa.collect_values(str(filesdir / Path("imported.wdl")), True,
                                   "category", "other", "description", "...",
                                   False, True, True)
    with pytest.raises(ValueError):
        values = wa.collect_values(str(filesdir / Path("no_output_parameter_meta.wdl")), True,
                                   "category", "other", "description", "...",
                                   False, True, True)


def test_collect_values_strict_inputs():
    with pytest.raises(ValueError):
        values = wa.collect_values(str(filesdir / Path("imported.wdl")), True,
                                   "category", "other", "description", "...",
                                   False, True, False)
    wa.collect_values(str(filesdir / Path("no_output_parameter_meta.wdl")), True,
                                   "category", "other", "description", "...",
                                   False, True, False)



def test_collect_values_strict_outputs():
    with pytest.raises(ValueError):
        values = wa.collect_values(str(filesdir / Path("no_output_parameter_meta.wdl")), True,
                                   "category", "other", "description", "...",
                                   False, False, True)
    wa.collect_values(str(filesdir / Path("imported.wdl")), True,
                                   "category", "other", "description", "...",
                                   False, False, True)


def test_no_workfow():
    with pytest.raises(ValueError):
        values = wa.collect_values(str(filesdir / Path("no_workflow.wdl")),
                                   True, "category", "other", "description",
                                   "...", False, False, False)


def test_main_defaults(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl"))]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected.md")).open("r") as expected_output:
        expected = expected_output.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_no_required(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--do-not-separate-required"]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected_no_required.md")).open("r") as expected_output:
        expected = expected_output.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_keys(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--description-key", "desc", "--category-key", "cat"]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected_keys.md")).open("r") as expected_output:
        expected = expected_output.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_fallback(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--fallback-description", "...",
                "--fallback-category", "advanced",
                "--fallback-description-to-object"]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected_fallback.md")).open("r") as expected_output:
        expected = expected_output.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_template(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--template", str(filesdir / Path("test.template"))]
    wa.main()
    captured = capsys.readouterr()
    with (filesdir / Path("test.template")).open("r") as expected_output:
        expected = expected_output.read()
    assert captured.out == expected


def test_main_output(tmpdir):
    output_file = tmpdir.join("output.md")
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "-o", output_file.strpath]
    wa.main()
    with output_file.open() as out_file:
        result = out_file.readlines()
    with (filesdir / Path("expected.md")).open("r") as expected_output:
        expected = expected_output.readlines()[:-1]
    assert result == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_extra(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "-t", str(filesdir / Path("extra.template")),
                "-e", str(filesdir / Path("extra.json"))]
    wa.main()
    captured = capsys.readouterr()
    with (filesdir / Path("extra.json")).open("r") as expected_output:
        expected = expected_output.read()
    assert captured.out == expected


def test_main_strict():
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")), "--strict"]
    with pytest.raises(ValueError) as e:
        wa.main()
    assert e.value.args[0] == ("Missing parameter_meta for inputs:\n"
                               "test.echo.missingDescription\n"
                               "test.sw.workflowOptional\n\n"
                               "Missing parameter_meta for outputs:\n"
                               "test.output2")

def test_main_strict_inputs():
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")), "--strict-inputs"]
    with pytest.raises(ValueError) as e:
        wa.main()
    assert e.value.args[0] == ("Missing parameter_meta for inputs:\n"
                               "test.echo.missingDescription\n"
                               "test.sw.workflowOptional")

def test_main_strict_outputs():
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")), "--strict-outputs"]
    with pytest.raises(ValueError) as e:
        wa.main()
    assert e.value.args[0] == ("Missing parameter_meta for outputs:\n"
                               "test.output2")