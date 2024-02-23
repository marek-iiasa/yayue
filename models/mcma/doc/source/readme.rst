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

NOTE: all commands described in this Guide should be executed in a terminal
window.
In the commands explained below the $-character stands for the terminal prompt.

In orderr to avoid possible conflicts with already installed packages,
we recommend to create a dedicated conda environment for pyMCMA.
Preparation of the conda environment consists of two steps:

#. Create a dedicated conda environment for pymcma
    In the Guide we named such environment ``pymcma``. However, also other names can
    be used.
    Execute the following command:

    .. code-block:: console

        $ conda create --name pymcma -c conda-forge python=3.11

#. Update of the conda version.
    Execute the following command:

    .. code-block:: console

        $ conda update -n base -c conda-forge conda


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

The installation shall be done by executing at the terminal prompt the following
two commands (the first one should be skipped, if the pymcma is active in the
currently used terminal window:

.. code-block:: console

    $ conda activate pymcma
    $ pip install pymcma

Testing the installation
^^^^^^^^^^^^^^^^^^^^^^^^
The installation shall be tested by running the following two steps:

#. Creating work-space for initial analysis:
    .. code-block:: console

        $ pymcma --install

    This command creates in the current directory the initial work-space
    composed of three folders:

    #. Models - it contains the testing model.

    #. anaTst - folder and configuration of the testing analysis.

    #. Templates -folder with templates of configuration file and of Pyomo model.

#. Running the provided example of MCMA of the Pipa model outlined in the paper:
    .. code-block:: console

        $ pymcma --anaDir anaTst

    Successful installation shall result in computation of the Pareto-front for the
    tutorial model (included in the working space installation) and the analysis
    configuration specified ``anaTst/cfg.yml`` file.
    The standard output will be displayed in the terminal.

    After the computation of the Pareto-front representation will be completed,
    four plots (similar to those shown in the paper) will be displayed.
    The parallel plot is interactive, i.e., one can change (by moving the upper and/or
    lower end of the slider) the range of achievements of the cost critetion.
    Closing all windows with plots will terminate the execution.
    The default analysis results will be stored in the analysis directory,
    i.e., anaTst/Results.

Ready to go
-----------
Successful pyMCMA installation needs be done only once on each computer.
The pyMCMA will be available for use with diverse models.
For each model one can make many analyses.
All analyses can be made in one working space or in dedicated working spaces.
The latter can be created by installing new working space in another directory.

Actual use of pyMCMA for Multiple-Criteria Model Analysis is documented
in :doc:`user_guide`.

