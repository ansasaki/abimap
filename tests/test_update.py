#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for update command"""

from conftest import run_tc


def test_update(testcases, datadir, capsys, caplog):
    for tc in testcases:
        run_tc(tc, datadir, capsys, caplog)
