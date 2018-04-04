#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test for check_files function"""

import filecmp
import os

from symbol_version import symbol_version


def test_different_non_existent_files(datadir):
    in_name = os.path.join(str(datadir), "in.map")
    out_name = os.path.join(str(datadir), "new.map")

    symbol_version.check_files("--out", str(out_name),
                               "--in", str(in_name), False)

    symbol_version.check_files("--out", str(out_name),
                               "--in", str(in_name), True)


def test_different_overwrite(datadir):
    in_name = os.path.join(str(datadir), "in.map")
    out_name = os.path.join(str(datadir), "out.map")

    symbol_version.check_files("--out", str(out_name),
                               "--in", str(in_name), False)

    symbol_version.check_files("--out", str(out_name),
                               "--in", str(in_name), True)


def test_same_file(datadir, capsys):

    in_name = os.path.join(str(datadir), "in.map")

    input_name = str(in_name)

    # Running with "--dry" the files are not modified (the warning is given)
    symbol_version.check_files("--out", input_name,
                               "--in", input_name, True)

    # Capture stdout and stderr
    out, err = capsys.readouterr()

    # Compare the expected result with the provided one
    expected = "[WARNING] Given paths in \'--out\' and \'--in\' are the same.\n"
    assert err == expected
    assert out == ""

    # Running without "--dry"
    symbol_version.check_files("--out", input_name,
                               "--in", input_name, False)

    # Capture output messages
    out, err = capsys.readouterr()

    # Check expected warning
    expected = "".join(["[WARNING] Given paths in \'--out\' and \'--in\'",
                        " are the same.\n",
                        "[WARNING] Moving ",
                        "\'", input_name, "\' to ",
                        "\'", input_name, ".old\'.\n"])
    assert err == expected

    # Check expected message
    assert out == ""

    # Check if the file was created
    created = os.path.join(str(datadir), "in.map.old")
    assert os.path.isfile(created)

    # Check the content
    assert filecmp.cmp(in_name, created, shallow=False)
