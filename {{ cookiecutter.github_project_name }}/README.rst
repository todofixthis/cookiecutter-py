.. image:: https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/actions/workflows/build.yml/badge.svg
   :target: https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/actions/workflows/build.yml
.. image:: https://readthedocs.org/projects/{{ cookiecutter.pypi_project_name }}/badge/?version=latest
   :target: http://{{ cookiecutter.pypi_project_name }}.readthedocs.io/

{{ cookiecutter.project_name }}
{{ '=' * cookiecutter.project_name|length }}

{{ cookiecutter.project_short_description }}

Getting Started
---------------
TODO

Requirements
------------
{{ cookiecutter.project_name }} is known to be compatible with the following Python versions:

- {{ cookiecutter.python_version }}
- {{ cookiecutter.__python_major }}.{{ cookiecutter.__python_minor | int - 1 }}
- {{ cookiecutter.__python_major }}.{{ cookiecutter.__python_minor | int - 2 }}

.. note::

   I'm only one person, so to keep from getting overwhelmed, I'm only committing to
   supporting the 3 most recent versions of Python.

Maintainers
-----------
To install the distribution for local development, some additional setup is required:

#. `Install uv <https://docs.astral.sh/uv/getting-started/installation/>`_ (only needs to be
   done once).

#. Run the following command to install additional dependencies::

      uv sync --group=dev

#. Activate pre-commit hook::

      uv run autohooks activate --mode=pythonpath

Running Unit Tests and Type Checker
-----------------------------------
Run the tests for all supported versions of Python using
`tox <https://tox.readthedocs.io/>`_::

   uv run tox -p

.. note::

   The first time this runs, it will take awhile, as mypy needs to build up its cache.
   Subsequent runs should be much faster.

If you just want to run unit tests in the current virtualenv (using
`pytest <https://docs.pytest.org>`_)::

   uv run pytest

If you just want to run type checking in the current virtualenv (using
`mypy <https://mypy.readthedocs.io>`_)::

   uv run mypy src test

Documentation
-------------
To build the documentation locally:

#. Switch to the ``docs`` directory::

    cd docs

#. Build the documentation::

    uv run make html

Releases
--------
Steps to build releases are based on
`Packaging Python Projects Tutorial <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`_.

.. important::

   Make sure to build releases off of the ``main`` branch!

One-time Setup
~~~~~~~~~~~~~~
#. Install the ``keyring`` tool and add it to your ``PATH``::

      uv tool install keyring
      uv tool update-shell

   Restart your shell after running ``update-shell``.
#. `Create a PyPI API token <https://pypi.org/manage/account/#api-tokens>`_ and store it
   in the OS keychain::

      keyring set https://upload.pypi.org/legacy/ __token__

   Paste the ``pypi-...`` token when prompted.

1. Build the Project
~~~~~~~~~~~~~~~~~~~~~
#. Delete artefacts from previous builds, if applicable::

    rm dist/*

#. Run the build::

    uv build

#. The build artefacts will be located in the ``dist`` directory at the top level of the
   project.

2. Upload to PyPI
~~~~~~~~~~~~~~~~~
#. Bump the version (also updates ``uv.lock``)::

      uv version <version>

#. Upload build artefacts to PyPI::

    uv publish --username __token__

3. Create GitHub Release
~~~~~~~~~~~~~~~~~~~~~~~~
#. Create a tag and push to GitHub::

      git tag -a <version> -m "Release <version>"
      git push origin <version>

#. Go to the `Releases page for the repo`_.
#. Click ``Draft a new release``.
#. Select the tag that you created above.
#. Specify the title of the release (e.g., ``{{ cookiecutter.project_name }} v1.2.3``).
#. Write a description for the release.  Make sure to include:
   - Credit for code contributed by community members.
   - Significant functionality that was added/changed/removed.
   - Any backwards-incompatible changes and/or migration instructions.
   - SHA256 hashes of the build artefacts.
#. GPG-sign the description for the release (ASCII-armoured).
#. Attach the build artefacts to the release.
#. Click ``Publish release``.

.. _Releases page for the repo: https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/releases
