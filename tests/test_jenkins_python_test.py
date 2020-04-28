#!/usr/bin/env python

"""Tests for `jenkins_python_test` package."""

import pytest


from jenkins_python_test import jenkins_python_test


def test_content(response):
    assert(2+2 == 4)
