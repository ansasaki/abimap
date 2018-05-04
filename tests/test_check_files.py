#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test for check_files function"""

import filecmp
import os

from smap import symver


def test_different_non_existent_files(datadir):
    in_name = os.path.join(str(datadir), "in.map")
    out_name = os.path.join(str(datadir), "new.map")

    symver.check_files("--out", str(out_name),
                       "--in", str(in_name), False)

    symver.check_files("--out", str(out_name),
                       "--in", str(in_name), True)


def test_different_overwrite(datadir):
    in_name = os.path.join(str(datadir), "in.map")
    out_name = os.path.join(str(datadir), "out.map")

    symver.check_files("--out", str(out_name),
                       "--in", str(in_name), False)

    symver.check_files("--out", str(out_name),
                       "--in", str(in_name), True)


def test_same_file(datadir, caplog):

    in_name = os.path.join(str(datadir), "in.map")

    input_name = str(in_name)

    # Running with "--dry" the files are not modified (the warning is given)
    symver.check_files("--out", input_name,
                       "--in", input_name, True)

    # The expected message
    expected = "".join(["Given paths in '--out' and '--in'",
                        " are the same."])

    # Check if the expected warning is in the log records
    for record in caplog.records:
        assert record.levelname != "CRITICAL"
        assert record.levelname != "ERROR"
    assert "WARNING  " + expected in caplog.text

    # Clear the captured log to not affect the following checks
    caplog.clear()

    # Running without "--dry"
    symver.check_files("--out", input_name,
                       "--in", input_name, False)

    # Check expected warning
    expected = "".join(["Moving ",
                        "\'", input_name, "\' to ",
                        "\'", input_name, ".old\'.\n"])

    # Check if the expected warning is in the log records
    for record in caplog.records:
        assert record.levelname != "CRITICAL"
        assert record.levelname != "ERROR"
    assert "WARNING  " + expected in caplog.text

    # Check if the file was created
    created = os.path.join(str(datadir), "in.map.old")
    assert os.path.isfile(created)

    # Check the content
    assert filecmp.cmp(in_name, created, shallow=False)
