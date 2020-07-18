.. _tips:

Some general recommendations in the Python ecosystem
====================================================

If you are new to Python, here are some tools you should look into:

* The `Interactive Python shell <https://ipython.org/>`_ (IPython). It enriches the
  `REPL <https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop>`_ interaction
  with syntax highlighting, tab completion, comprehensive object introspection,
  input and output history, much more readable stack traces, etc. (see 
  `list of features <https://ipython.readthedocs.io/en/stable/>`_).
* `Jupyter <https://jupyter.org/>`_ and `JupyterLab <https://jupyter.org/try>`_. They
  bring a Matlab-like notebook-oriented interface which allows for writing high-quality
  documents with mixture of code, output and Latex/Rich text documentation. These
  notebooks can be rendered as websites and shared easily.
  Most noteworthly, they allow interactivity in cells, such as sliders and animations.
  There is a whole universe to explore once you look for Jupyter notebooks. And
  you can easily `host your own notebooks in the cloud <https://mybinder.org/>`_.
* The `Python debugger <https://docs.python.org/3/library/pdb.html>`_ can come in handy
  in case of errors. With IPython, it's just the four letters ``%pdb`` away.
* If you look for plotting, `Matplotlib <https://matplotlib.org/>`_ is the defacto
  standard. Being part of Scipy, it depends on `Numpy <https://numpy.org/>`_, which
  provides N-dimensional arrays, linear algebra and input/output. When it comes to
  scientific computing, Numpy got some kind of hub and it's website lists dozens of
  related projects within all sciences.
