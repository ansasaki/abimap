#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for clean_symbols function"""

from symbol_version import symbol_version


def test_clean_symbols(testcases):
    if testcases:
        for tc in testcases:
            print("Test case: ", str(tc))
            assert (symbol_version.clean_symbols(tc["input"]) ==
                    tc["output"])
    else:
        # If no test cases were found, fail
        assert 0
