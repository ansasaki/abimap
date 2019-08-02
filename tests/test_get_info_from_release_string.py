# -*- coding: utf-8 -*-

"""Tests for test_get_info_from_release_string()"""

import pytest
from conftest import is_warning_in_log

from abimap import symver


@pytest.mark.skipif(pytest.__version__ < '3.4', reason="caplog not supported")
def test_get_info_from_release_string(testcases, caplog):
    if testcases:
        for tc in testcases:
            if tc["exceptions"]:
                with pytest.raises(Exception) as e:
                    assert (symver.get_info_from_release_string(tc["input"]) ==
                            tc["output"])
                    for expected in tc["exceptions"]:
                        assert expected in str(e.value)
                    if tc["warnings"]:
                        for expected in tc["warnings"]:
                            assert is_warning_in_log(expected, caplog.text)
            else:
                assert (symver.get_info_from_release_string(tc["input"]) ==
                        tc["output"])
                if tc["warnings"]:
                    for expected in tc["warnings"]:
                        assert is_warning_in_log(expected, caplog.text)

            # Clear the captured log and output so far
            caplog.clear()
    else:
        # If no test cases were found, fail
        assert 0
