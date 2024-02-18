About
=====

PyMCMA is the Python package for generation of uniformly distributed Pareto-efficient
solutions.

Installation
------------

Installation consists of the following steps run in a terminal window in the
working space. In the commands explained below the $-character stands for
the terminal prompt.

1. Installation of the pyMCMA package
    PyMCMA software should be installed within the conda environment created for
    Python version 3.11 using pip:

.. code-block:: console

    $ pip install pymcma

2. Installation of the working space
    TODO AS: add here info on installing package(?) or downloadding and unpacking
    a zip file with the working space dir-structure

    The working space is composed of the directory structure described in
    the :doc:`user_guide`.
    It provide space for actual use of pyMCMA, as well as a configuration of the
    easy to run installation test.
3. Testing the installation
    The installation shall be tested by running in the working space:

.. code-block:: console

    $ python -m pymcma

Successful installation shall result in computation of the Pareto-front for the
tutorial model (included in the working space installation) and the analysis
configuration specified for the default user named ``tst_usr``.
The standard output will be displayed in the terminal.
After the computation will be completed, four plots (similar to those shown in
the paper) will be displayed.
The parallel plot is interactive, i.e., one can change (by moving the upper and/or
lower end of the slider) the range of achievements of the cost critetion.
Closing all windows with plots will terminate the execution.
The default analysis results will be stored in the default-user data-space,
i.e., in the subdirectory Data/tst_usr of the working space.

Actual Multiple-Criteria Model analysis is documented in :doc:`user_guide`.

