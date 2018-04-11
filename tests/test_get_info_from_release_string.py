#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for test_get_info_from_release_string()"""

from symbol_version import symbol_version


def test_get_info_from_release_string(testcases):
    if testcases:
        for tc in testcases:
            if tc["exceptions"]:
                with pytest.raises(Exception) as e:
                    assert (symbol_version.get_info_from_release_string(tc["input"]) ==
                            tc["output"])
                    for expected in tc["exceptions"]:
                        assert expected in str(e.value)
                    if tc["warnings"]:
                        for expected in tc["warnings"]:
                            assert "WARNING  " + expected in caplog.text
            else:
                assert (symbol_version.get_info_from_release_string(tc["input"]) ==
                        tc["output"])
                if tc["warnings"]:
                    for expected in tc["warnings"]:
                        assert "WARNING  " + expected in caplog.text
                    tc["output"])
    else:
        # If no test cases were found, fail
        assert 0
