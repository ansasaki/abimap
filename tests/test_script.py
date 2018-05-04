# /usr/bin/env python
# -*- coding: utf-8 -*-

"""Test running as a command line script"""

from conftest import cd


def run_script(testcases, datadir, script_runner, capsys, caplog, script):
    for tc in testcases:
        with cd(datadir):
            tc_in = tc["input"]
            tc_out = tc["output"]
            args = tc_in["args"]
            tc_stdin = tc_in["stdin"]

            ret = None
            if tc_stdin:
                with open(tc_stdin, "r") as tcin:
                    # Run the script passing the arguments
                    if args:
                        ret = script_runner.run(script, *args, stdin=tcin)
                    else:
                        ret = script_runner.run(script, stdin=tcin)
                    if not ret.success:
                        print(ret.returncode)
                        print(ret.stdout)
                        print(ret.stderr)
                        assert 0
            else:
                print("Missing input file")
                assert 0

            assert ret.success

            # If there is an expected output to stdout
            if tc_out["stdout"]:
                with open(tc_out["stdout"], "r") as tcout:
                    expected = tcout.read()
                    assert ret.stdout == expected
            else:
                if ret.stdout:
                    print(tc)
                    print("Unexpected output in stdout:\n" + ret.stdout)
                    # Fail
                    assert 0

            # Check if the expected warning messages are in the log
            if tc_out["warnings"]:
                for expected in tc_out["warnings"]:
                    assert expected in caplog.text

            # Check if the expected exception messages are in the log
            if tc_out["exceptions"]:
                for expected in tc_out["exceptions"]:
                    assert expected in caplog.text

            # Clear the log between test cases
            caplog.clear()


def test_main(testcases, datadir, script_runner, capsys, caplog):
    run_script(testcases, datadir, script_runner, capsys, caplog, "smap")
