from setuptools import setup

# For good setup.py templates, see also
# https://github.com/navdeep-G/setup.py/blob/master/setup.py

optional_packages = {
   "scipy": ["scipy"],
   "graphs": ["networkx", "pyGraphViz"],
}

setup(
   name='PyDDA',
   version='0.10101',
   description='The digital differential analyzer python implementation',
   license="GPL et al",
   long_description=open("README.md", "r").read(),
   author='Anadigm',
   author_email='koeppel@analogparadigm.com',
   url="http://www.anadigm.com/",
   packages=['PyDDA'],
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
)
