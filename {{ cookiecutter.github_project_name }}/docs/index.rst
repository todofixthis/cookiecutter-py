{{ cookiecutter.project_name }}
{{ '=' * cookiecutter.project_name|length }}

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   api

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
