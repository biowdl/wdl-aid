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

import WDL

import wdl_aid.wdl_aid as wa

filesdir = Path(__file__).parent / Path("files")


def test_fully_qualified_inputs():
    doc = WDL.load(str(filesdir / Path("workflow.wdl")))
    available_inputs = doc.workflow.available_inputs
    qualified_names = wa.fully_qualified_inputs(available_inputs,
                                                doc.workflow.name)
    assert [x[0] for x in qualified_names] == ['test.sw.workflowOptional',
                                               'test.echo.missingDescription',
                                               'test.echo.taskOptional',
                                               'test.input2',
                                               'test.input1']


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
                                   "cat": "common"}
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


def test_main_defaults(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl"))]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected.md")).open("r") as expected_ouput:
        expected = expected_ouput.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_no_required(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--do-not-separate-required"]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected_no_required.md")).open("r") as expected_ouput:
        expected = expected_ouput.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_keys(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--description-key", "desc", "--category-key", "cat"]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected_keys.md")).open("r") as expected_ouput:
        expected = expected_ouput.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_fallback(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--fallback-description", "...",
                "--fallback-category", "advanced",
                "--fallback-description-to-object"]
    wa.main()
    captured = capsys.readouterr().out.splitlines(True)
    with (filesdir / Path("expected_fallback.md")).open("r") as expected_ouput:
        expected = expected_ouput.readlines()[:-1]
    assert captured == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]


def test_main_template(capsys):
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "--template", str(filesdir / Path("test.template"))]
    wa.main()
    captured = capsys.readouterr()
    with (filesdir / Path("test.template")).open("r") as expected_ouput:
        expected = expected_ouput.read()
    assert captured.out == expected


def test_main_output(tmpdir):
    output_file = tmpdir.join("output.md")
    sys.argv = ["script", str(filesdir / Path("workflow.wdl")),
                "-o", output_file.strpath]
    wa.main()
    with output_file.open() as out_file:
        result = out_file.readlines()
    with (filesdir / Path("expected.md")).open("r") as expected_ouput:
        expected = expected_ouput.readlines()[:-1]
    assert result == expected + ["> Generated using WDL AID ({})\n".format(wa.__version__)]
