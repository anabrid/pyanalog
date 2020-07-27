#!/usr/bin/env python3

from setuptools import setup

# For good setup.py templates, see also
# https://github.com/navdeep-G/setup.py/blob/master/setup.py

optional_packages = {
   "fpaa": ["pyYAML"], # actually required for fpaa
   "scipy": ["scipy"], # in general strongly recommended
   "graphs": ["networkx", "pyGraphViz"],
   "makedocs": ["sphinx"],
   "runtests": ["pytest"],
}

setup(
   name="pyanalog", # TODO choose some generic name
   version='0.10101',
   description='The digital differential analyzer python implementation',
   license="GPL et al",
   long_description=open("README.md", "r").read(),
   author='Anadigm',
   author_email='koeppel@analogparadigm.com',
   url="http://www.anadigm.com/",
   packages=["dda", "fpaa", "hycon"],
   extras_require=optional_packages,
   install_requires=[], # no external dependencies :-)
   scripts=[], # should collect some wannabe-$PATH scripts below scripts/
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },

    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
      #  'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Pre-processors'
    ],


    # Can also add tests:
#    setup_requires=['pytest-runner'],
#    tests_require=['pytest'],
)
