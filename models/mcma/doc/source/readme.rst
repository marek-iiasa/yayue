About
=====

PyMCMA is the Python package for generation of uniformly distributed Pareto-efficient
solutions.

Requirements
------------

PyMCMA can be installed on computers running one of the following OS:
macOS, Linux, Ms-Windows.
It was tested with the Conda environment on each of these OSs.
All required conda packages are installed during the PyMCMA installation.

Installation
------------

Installation consists of the following steps:

#. Creating and/or activating the Conda environment

#. Installation of the pyMCMA

#. Creation of the work-space

#. Testing the installation

Each of these steps is described in the corresponding section below.

Conda environment
^^^^^^^^^^^^^^^^^
Conda is widely used, it is available for macOS, Linux, and MS-Windows;
it supports easy organization of dedicated (when needed) environments for diverse
packages, as well as easy updates of packages with keeping consistency of their
versions.
Conda documentation is available at: https://docs.conda.io/en/latest/

NOTE: all commands described in this Guide should be executed in a terminal window.
In the commands explained below the $-character stands for the terminal prompt.
The actual terminal prompt depends on the OS and setup of the user environment.

In order to avoid possible conflicts with already installed packages,
we recommend to install and use the pyMCMA within a dedicated and regularly updated
conda environment created for Python version 3.11.

Preparation of the conda environment consists of two steps:

#. Create a dedicated conda environment for pymcma
    Execute the following command:

    .. code-block:: console

        $ conda create --name pymcma -c conda-forge python=3.11

    The dedicated pyMCMA environment is named here ``pymcma``.
    However, another name can be used.

#. Update of the conda version.
    Execute the following command:

    .. code-block:: console

        $ conda update -n base -c conda-forge conda


The dedicated conda environment should be activated whenever the pymcma is
executed by the command-line.
The environment should also be specified for the core (substantive) model
development (see the :doc:`user_guide` for details).

pyMCMA installation
^^^^^^^^^^^^^^^^^^^
PyMCMA software (further on referred as ``pymcma``, the name used for its execution)
should be installed by running the below specified commands.
The commands should be executed in a terminal window within the activated conda
environment.
In the commands explained below the $-character stands for the terminal prompt.

The installation shall be done by executing at the terminal prompt the following
two commands (the first one should be skipped, if the conda pymcma environment
is active in the currently used terminal window):

.. code-block:: console

    $ conda activate pymcma
    $ pip install pymcma

The installation will include all packages necessary for running pyMCMA,
as well as assuring the consistent versions of all packages.
We recommend to follow the good practice of updating the software, i.e.,
to periodically execute:

.. code-block:: console

    $ conda update --all

After the pyMCMA installation any other conda packages desired by the user can
be installed in the usual way, i.e.,

.. code-block:: console

    $ conda install xxx, yyy

where xxx, yyy are names of the desired packages.
The above recommended installation sequence assures the version consistency of
all packages within the ``pymcma`` conda environment, not only during the installation
but also during periodical updates of the environment.

Creation of the work-space
^^^^^^^^^^^^^^^^^^^^^^^^^^
The work-space for initial analysis can be created by running:

.. code-block:: console

    $ pymcma --install

This command creates in the current directory the initial work-space
composed of three folders:

#. Models - it contains the test-model.
    The name of the provided model should not be changed unless the
    corresponding modification is done in''anaTst/cfg.yml`` file.

#. anaTst - folder for and configuration of the testing analysis.
    Note that the analysis configuration is prepared in ''anaTst/cfg.yml`` file
    assuming that neither the ``Models`` directory nor the test model is moved.

#. Templates - folder with templates of configuration file and of Pyomo model.
    This directory can be moved to any place the user prefers.
    The two provided templates, namely example.py and cfg.yml, might help in
    development of actual core-model instances, and in configuration
    of actual analyses.


Testing the installation
^^^^^^^^^^^^^^^^^^^^^^^^
Testing consists of running the preconfigured analysis of the provided core-model
example of the Pipa model outlined in the paper.
To following command runs the analysis:

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

One can easily experiment with diverse configurations of the analysis by
creating for each analysis a dedicated folder, editing the configuration,
and running the analysis.
Assuming that next analysis will be done in directory ``myAnal`` and thet
the standard unix vi editor is used for editing the configuration file,
one can execute the following commands:

.. code-block:: console

    $ mkdir myAnal
    $ cp anaTst/cfg.yml myAnal/cfg.yml
    $ vi myAnal/cfg.yml
    $ pymcma --anaDir myAnal

Configuration of analysis is discussed in detail in :doc:`user_guide`.

Ready to go
-----------
Successful pyMCMA installation needs be done only once on each computer.
The pyMCMA will be available for use with diverse models.
For each model one can make many analyses.
All analyses can be made in one working space or in dedicated working spaces.
The latter can be created by installing new working space in another directory.

Actual use of pyMCMA for Multiple-Criteria Model Analysis is documented
in :doc:`user_guide`.

