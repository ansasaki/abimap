# -*- coding: utf-8 -*-

"""Tests for update command"""

import pytest
from conftest import run_tc


@pytest.mark.skipif(pytest.__version__ < '3.4', reason="caplog not supported")
def test_update(testcases, datadir, capsys, caplog):
    for tc in testcases:
        run_tc(tc, datadir, capsys, caplog)
