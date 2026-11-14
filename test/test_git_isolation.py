"""Tests for the git isolation every test runs under."""

import os

from plumbum import local


def test_copier_git_sees_isolated_environment() -> None:
    """copier's git, run through plumbum, gets the isolated environment.

    plumbum copies the environment at import, so patching ``os.environ``
    alone would leave copier's git reading the runner's own setup.
    """
    assert local.env.get("GIT_CONFIG_GLOBAL") == os.devnull
    assert local.env.get("GIT_CONFIG_NOSYSTEM") == "1"
    assert local.env.get("XDG_CONFIG_HOME") == os.environ["XDG_CONFIG_HOME"]
