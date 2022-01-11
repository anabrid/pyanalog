# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sys, os
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project   = 'PyAnalog'
copyright = '2022, Anabrid GmbH'
author    = 'The Analog People'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
   'sphinx.ext.autodoc',
   'sphinx.ext.viewcode',
   'sphinx.ext.autosummary',
   'sphinx.ext.mathjax',

   # Mermaid diagrams
   # pip install sphinxcontrib-mermaid
   # https://github.com/mgaitan/sphinxcontrib-mermaid
#   'sphinxcontrib.mermaid',

   # Jupyter Notebooks in sphinx
   'nbsphinx',
   
   
   # Allow SVGs in the PDF make target
   # https://github.com/missinglinkelectronics/sphinxcontrib-svg2pdfconverter
   'sphinxcontrib.rsvgconverter',  # not yet included into the docker image
   # Problem with the generated SVGs within PDFs: Size ist not preserved, small figures
   # are filling whole pages.

   # Instead, builtin and cheap SVG to PNG:
   #'sphinx.ext.imgconverter',
   # Same problem as above but worse quality

   # Pygments lexer ipython3
   # https://github.com/spatialaudio/nbsphinx/issues/24
  'IPython.sphinxext.ipython_console_highlighting'   # also not yet included in the docker image
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_member_order = "bysource"

# Solves "Sphinx Error contents.rst not found" on some systems, see
# https://stackoverflow.com/a/56448499
master_doc = "index"

#mermaid_pdfcrop = "pdfcrop"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

#html_theme = 'alabaster' # = default
html_theme = 'sphinx_rtd_theme' # Read the docs theme, nicer.

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for nbsphinx input --------------------------------------------------

nbsphinx_execute = 'never'  # we expect all notebooks to have output stored

# Otherwise we could do this:
#nbsphinx_execute_arguments = [
#    "--InlineBackend.figure_formats={'svg', 'pdf'}",
#    "--InlineBackend.rc={'figure.dpi': 96}",
#]


# -- Options for PDF output --------------------------------------------------

latex_preamble = r'''
\setcounter{tocdepth}{2}

% Fix for allowing to show unicode delta character 
% See also option 'textgreek' in latex_elements
% (https://www.sphinx-doc.org/en/master/latex.html#latex-elements-confval)
\DeclareUnicodeCharacter{0394}{\ensuremath{\Delta}}

% another fix for minimal length bug
\setlength{\headheight}{14pt} % https://tex.stackexchange.com/a/198694

% another fix for very long equations
\allowdisplaybreaks % https://tex.stackexchange.com/a/51883
'''

latex_elements = {
    'papersize': 'a4paper',  # default
    'pointsize': '11pt',     # default is microscopic 10pt
    'preamble': latex_preamble,
    'fncychap':  '\\usepackage[Bjornstrup]{fncychap}'  # cf https://ctan.mirror.norbert-ruehl.de/macros/latex/contrib/fncychap/fncychap.pdf
}

latex_show_pagerefs = True
latex_show_urls = 'footnote'

# we introduce chapters by our own.
# This is an ugly workaround since RTD otherwise makes way too many chapters.
# See also index.rst for raw latex \chapters.
latex_toplevel_sectioning = "section"

# SVG to PDF conversion for Latex output
rsvg_converter_args = [ "--dpi-x=300", "--dpi-y=300", "--keep-aspect-ratio" ]

# Options for the RTD ("Read the docs") sphinx theme
# all these do not work!
#html_theme_options = {
#    'display_github': True
#}
#html_contenxt = {
#    'source_url_prefix': "https://github.com/anabrid/pyanalog/tree/master/doc",
#}
#---> overwriting _templates/breadcrumbs.html instead, see the similar named file in
#     this directory.
