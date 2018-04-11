#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from symbol_version import symbol_version


def test_get_version_from_string(testcases, caplog):
    if testcases:
        for tc in testcases:
            if tc["exceptions"]:
                with pytest.raises(Exception) as e:
                    assert (symbol_version.get_version_from_string(tc["input"]) ==
                            tc["output"])
                    for expected in tc["exceptions"]:
                        assert expected in str(e.value)
                    if tc["warnings"]:
                        for expected in tc["warnings"]:
                            assert "WARNING  " + expected in caplog.text
            else:
                assert (symbol_version.get_version_from_string(tc["input"]) ==
                        tc["output"])
                if tc["warnings"]:
                    for expected in tc["warnings"]:
                        assert "WARNING  " + expected in caplog.text
    else:
        # If no test cases were found, fail
        assert 0
