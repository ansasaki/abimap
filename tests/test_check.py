#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for check command"""

import os

import pytest
from conftest import cd

from smap import symver


def run_tc(tc, datadir, capsys, caplog):
    """
    Run a 'check' command test case

    :param tc: The tescase
    :param datadir: The path to the directory where the test input are
    :param capsys: The output capture fixture
    :param caplog: The log capture fixture
    """

    # Change directory to the temporary directory
    with cd(datadir):
        # Get a parser
        parser = symver.get_arg_parser()

        tc_in = tc["input"]
        tc_out = tc["output"]

        # Parse the testcase arguments
        args = parser.parse_args(tc_in["args"])

        # Call the function
        if tc_out["exceptions"]:
            with pytest.raises(Exception) as e:
                args.func(args)
            for expected in tc_out["exceptions"]:
                assert expected in str(e.value)
        else:
            args.func(args)

        # Check if the expected messages are in the log
        if tc_out["warnings"]:
            for expected in tc_out["warnings"]:
                assert expected in caplog.text

        # If a log file was supposed to exist, check the content
        if args.logfile:
            if os.path.isfile(args.logfile):
                with open(args.logfile, "r") as log:
                    logged = log.read()
                    if tc_out["warnings"]:
                        for expected in tc_out["warnings"]:
                            assert expected in logged
                    if tc_out["exceptions"]:
                        for expected in tc_out["exceptions"]:
                            assert expected in logged
            else:
                if tc_out["warnings"] or tc_out["exceptions"]:
                    with capsys.disabled():
                        print(tc)
                        print("Expected to have a logfile:\n" + args.logfile)
                    # Fail
                    assert 0

        # Clear the captured log and output so far
        caplog.clear()


def test_check(testcases, datadir, capsys, caplog):
    for tc in testcases:
        run_tc(tc, datadir, capsys, caplog)
