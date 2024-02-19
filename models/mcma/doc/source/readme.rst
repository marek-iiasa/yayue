About
=====

PyMCMA is the Python package for generation of uniformly distributed Pareto-efficient
solutions.

Installation
------------

Installation consists of the following steps:

#. Creating and/or activating the Conda environment

#. Installation of the pyMCMA

#. Creation of the working space

#. Testing the installation

Each of these steps is described in the corresponding section below.

Conda environment
^^^^^^^^^^^^^^^^^
We recommend to install and use the pyMCMA within a dedicated and regularly updated
conda environment created for Python version 3.11.
Conda is widely used, it is available for macOS, Linux, and MS-Windows;
it supports easy organization of dedicated (when needed) environments for diverse
packages, as well as easy updates of packages with keeping consistency of their
versions.

Documentation of conda is available at ....

TODO: proper link to info on conda (maybe also a link to anaconda download page) should
be added above.

The dedicated conda environment should be activated whenever the pyMCMA is
executed by the command-line.
The environment should also be specified for the core (substantive) model
development.

pyMCMA installation
^^^^^^^^^^^^^^^^^^^
PyMCMA software should be installed by running the below specified commands.
The commands should be executed in a terminal window within the activated conda
environment.
In the commands explained below the $-character stands for the terminal prompt.

The installation consists of two steps:

#. Installation of the pyMCMA package
    Execute the following pip command:

.. code-block:: console

    $ pip install pymcma

    TODO something is wrong here: the above (and others) code-block needs to be
    properly terminated. Currently this comment is a part of the code; moreover,
    numbering the following items is destroyed.

#. Installation of the working space
    The first working space can be created in any folder in which the conda
    is accessible.
    We recommend to create a dedicated folder for the working space.

    TODO AS: add here info on installing package(?) or downloadding and unpacking
    a zip file with the working space dir-structure

    The working space is composed of the directory structure described in
    the :doc:`user_guide`.
    It provides space for actual use of pyMCMA, as well as a configuration of the
    easy to run installation test.

Testing the installation
^^^^^^^^^^^^^^^^^^^^^^^^
The installation shall be tested by running in the working space (created in
the second step described above):

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

Ready to go
-----------
Successful pyMCMA installation needs be done only once on each computer.
The pyMCMA will be available for use with diverse models.
For each model one can make many analyses.
All analyses can be made in one working space or in dedicated working spaces.
The latter can be created by installing new working space in another directory.

Actual use of pyMCMA for Multiple-Criteria Model Analysis is documented
in :doc:`user_guide`.

