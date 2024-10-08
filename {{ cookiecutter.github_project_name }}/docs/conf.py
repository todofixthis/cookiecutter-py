#!/usr/bin/env python3
# -- General configuration ------------------------------------------------
# The suffix(es) of source filenames. Provide a list to use multiple suffixes.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "{{ cookiecutter.project_name }}"
copyright = "{{ cookiecutter.this_year }} {{ cookiecutter.author_name }}"
author = "{{ cookiecutter.author_name }}"

# The language for content autogenerated by Sphinx. Refer to documentation for a list of
# supported languages.
#
# This is also used if you do content translation via gettext catalogs. Usually you set
# ``language`` from the command line for these cases.
language = 'en-NZ'

# List of patterns, relative to source directory, that match files and directories to
# ignore when looking for source files. This patterns also effect to
# ``html_static_path`` and ``html_extra_path``.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, ``todo`` and ``todoList`` produce output; else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for a list of
# builtin themes.
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Output file base name for HTML help builder.
htmlhelp_basename = "{{ cookiecutter.pypi_project_name }}doc"

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/{{ cookiecutter.python_version.split('.')[0] }}", None),
}

# -- Options for autodoc extension -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autodoc_default_options = {
    "members": True,
    "member-order": "alphabetical",
    "special-members": True,
    "undoc-members": True,
}

# -- Options for napoleon extension ------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration
napoleon_attr_annotations = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_type_aliases = None
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
