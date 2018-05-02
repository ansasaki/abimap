#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for bump version function"""

from smap import smap


def test_bump_version(testcases):
    if testcases:
        for tc in testcases:
            print("Test case: ", str(tc))
            assert (smap.bump_version(
                tc["input"][0], tc["input"][1]) ==
                tc["output"])
    else:
        # If no test cases were found, fail
        assert 0
