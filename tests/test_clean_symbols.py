#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for clean_symbols function"""

from smap import symver


def test_clean_symbols(testcases):
    if testcases:
        for tc in testcases:
            print("Test case: ", str(tc))
            assert (symver.clean_symbols(tc["input"]) ==
                    tc["output"])
    else:
        # If no test cases were found, fail
        assert 0
