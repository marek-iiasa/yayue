About
=====

PyMCMA is the Python package for generation of uniformly distributed Pareto-efficient
solutions.

Requirements
------------

PyMCMA can be installed on computers running one of the following OS:
macOS, Linux, MS-Windows.
It was tested with the conda environment on each of these OSs.
All required conda packages are installed during the PyMCMA installation.

Installation
------------

Installation consists of the following steps:

#. Creating and/or activating the Conda environment

#. Installation of the pyMCMA

#. Installation of the examples and templates

#. Execution of the provided example of analysis


Each of these steps is described in the corresponding section below.

Creating and/or activating the Conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

To be sure that everything will work as intended we highly recommend to use
the following ``.condarc`` configuration file:

.. code-block:: YAML

    ssl_verify: true
    channels:
      - conda-forge
      - defaults
    channel_priority: flexible
    auto_activate_base: false

Preparation of the conda environment consists of two steps:

#. Update of the conda version.
    Execute the following command:

    .. code-block:: console

        $ conda update -n base -c conda-forge conda


#. Create a dedicated conda environment for pyMCMA.
    Execute the following command:

    .. code-block:: console

        $ conda create --name pymcma -c conda-forge python=3.11

    The dedicated pyMCMA environment is named here ``pymcma``.
    However, another name can be used.

The dedicated conda environment should be activated whenever the ``pymcma`` is
executed by the command-line.
The environment should also be specified for the core (substantive) model
development (see the :doc:`user_guide` for details).

Installation of the pyMCMA
^^^^^^^^^^^^^^^^^^^^^^^^^^
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
    $ conda install pymcma

The installation will include all packages necessary for running ``pymcma``,
as well as assure version consistency of all packages installed
(and subsequently updated) in the created conda environment.
The installation can be tested by running:

.. code-block:: console

    $ pymcma -h

It should result in displaying the ``pymcma`` help consisting of the list
of available ``pymcma`` command-line options.

Note that the first run of the ``pymcma`` after its installation includes one-time
configuration of the installed software;
therefore, it takes much longer time (up to several minutes, depending the computer
resources) than subsequent runs.
Repeated execution of the above command should take about one second.

We recommend to follow the good practice of updating the software, i.e.,
to periodically execute:

.. code-block:: console

    $ conda update --all

After the pyMCMA installation any other conda packages desired by the user can
be installed in the usual way, i.e.,

.. code-block:: console

    $ conda install xxx yyy

where xxx, yyy are names of the desired packages.
The above recommended installation sequence assures the version consistency of
all packages within the ``pymcma`` conda environment, not only during the installation
but also during periodical updates of the environment.

Installing examples and templates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Installation of the provided examples and templates is optional.
They can be installed in any directory by the command:

.. code-block:: console

    $ pymcma --install

The provided examples are organized into three folders created in the
current directory:

#. ``Models/`` - it contains the test-model.
    The name of the provided model should not be changed unless the
    corresponding modification is done in ``anaTst/cfg.yml`` file.

#. ``anaTst/`` - folder for and configuration of the testing analysis.
    Note that the analysis configuration is prepared in ``anaTst/cfg.yml`` file
    assuming that neither the ``Models`` directory nor the test model is moved.

#. ``Templates/`` - folder with templates of configuration file and of Pyomo model.
    This directory can be moved to any place the user prefers.
    The two provided templates, namely ``example.py`` and ``cfg.yml``, might help in
    development of actual core-model instances, and in configuration
    of actual analyses.

Running the provided example of analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The preconfigured analysis of the provided core-model example of the Pipa
model outlined in the paper can be run in any directory where the ``anaTst/``
and ``Models/`` folders are available (e.g., by running the above presented
example installation).
The following command runs the analysis:

.. code-block:: console

    $ pymcma --anaDir anaTst

Successful run shall result in computation of the Pareto-front for the
tutorial model (included in the working space installation) and the analysis
configuration specified ``anaTst/cfg.yml`` file.
The standard output will be displayed in the terminal.

After the computation of the Pareto-front representation will be completed,
four plots (similar to those shown in the paper) will be displayed.
The parallel coordinates plot is interactive, i.e., one can change (by moving
the upper and/or lower end of the slider) the range of achievements of the
cost criterion. Closing all windows with plots will terminate the execution.
The default analysis results will be stored in the analysis directory,
i.e., ``anaTst/Results``.

Experimenting with diverse analyses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
One can easily experiment with diverse configurations of the analysis by
creating for each analysis a dedicated folder, editing the configuration,
and running the analysis.
Assuming that next analysis will be done in directory ``myAnal`` one can copy
and then edit the configuration file with their favorite text editor.
Note that the below shown ``cp ...`` command on the WindowsOS may have to
be modified.

.. code-block:: console

    $ mkdir myAnal
    $ cp anaTst/cfg.yml myAnal/cfg.yml

After editing and saving the configuration file, run the analysis using:

.. code-block:: console

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

