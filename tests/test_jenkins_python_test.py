#!/usr/bin/env python

"""Tests for `jenkins_python_test` package."""

import pytest


from jenkins_python_test import jenkins_python_test


def test_content():
    assert(4 == jenkins_python_test.add(2,2))
