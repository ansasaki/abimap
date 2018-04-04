#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unity tests"""

from symbol_version import symbol_version


def test_get_version_from_string(testcases):
    if testcases:
        for tc in testcases:
            print("Test case: ", str(tc))
            assert (symbol_version.get_version_from_string(tc["input"]) ==
                    tc["output"])
    else:
        # If no test cases were found, fail
        assert 0
