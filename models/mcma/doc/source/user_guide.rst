User Guide
==========
The ``pymcma`` .... (adapt from the paper)....

Overview of ``pymcma``
----------------------
Every Multiple-Criteria Model Analysis (MCMA) consists of two linked but
distinct tasks:

#. Development of a core model (aka substantive model)
    The model defines the relations between variables representing the criteria
    and all other variables (representing e.g., decisions, system state, etc).
    Discussion on methodology and tools for model development is beyond the
    ``pcmcma`` scope. Therefore, we present only the guidelines spacific for
    model preparation to the MCMA.

#. Computations of the Pareto-front representation.
    Each Pareto solution fits best the specified preferences.
    In interactive MCMA the preferences are specified by the users.
    The ``pcmcma`` generates preferences autonomously aiming at sequentially
    decreasing the maximum distance between neighbor solutions in order to provide
    a uniformly distributed representation of the Pareto-front.
    Therefore, the MCMA part is very easy; it requires only a configuration
    of the desired analysis.

Below we discuss the requirements for each of the above two tasks.
The ``pymcma`` supports seamless integratation of these two tasks, which makes
the objective (i.e., preference free) MCMA analysis very easy.

Issues common for both tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Both tasks should be done in terminal windows with the activated conda
environment created during the ``pymcma`` installation.
From the user point of view, the linkage between these task consists of
only specification of two items in the analysis configuration file.
Therefore, the model development and its analysis can be done in
different folders; actually, it also can be done on different computers,
possibly running different OSs.

Development of the core model
-----------------------------
The ``pymcma`` will process any model developed according to the good modeling
practice provided it conforms to the additional requirements specified below.
All but the first these requirements are typical for the MCMA tools and
are easy to conform to.

Modeling environment
^^^^^^^^^^^^^^^^^^^^
The ``pymcma`` can be integrated only with models developed in Pyomo,
the Python-based, open-source structured modeling language.
Pyomo is widely used, countless open-source models of diverse problems
are posted on the GitHub.
Actually, Pyomo provides a rich collection of classes, objects of which
provide building blocks for development of properly structured models.
Moreover, being Python-based, functionality of Pyomo can easily combined
with diverse Python-packages supporting wide range of various functionalities.
Therefore, the ``pymcma`` developers consider Pyomo as the best available
environment for development of algebraic models.
More information on, and downloads of Pyomo are available at www.pyomo.org

In particular, ``pymcma`` provides seamless integration with the core-model,
also, if it is developed on another computer, possibly under a different
operating system.
Pyomo provides this critically important feature.
Namely, two independently developed Pyomo concerete models can be
included as blocks into a new concrete model.
Such integration preserves name-spaces; therefore, there are no naming
conflicts, typical for other model-instance integration methods,
e.g., merging the MPS-files.

Variables representing criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
At least two core-model variables should be defined to be used as criteria.
Further on such variables are called ``outcome variables`` or (for short)
``outcomes``.
Such variables have to be scalar (i.e., not indexed) and have names conforming
to the traditional naming requirements: (1)~composed of only Latin letters and
(optionally) digits, and (2)~be maximum eight characters long.

One can define many ``outcomes``.
Actually, criteria are defined for each analysis; therefore, any core-model
variable conforming to the above requirements can serve as a criterion.
However, all variables intended to become criteria should be included in
the model testing.

Model testing
^^^^^^^^^^^^^
Before applying MCMA each model should pass comprehensive testing conforming
to the good modeling practice.
Testing should include single-criterion optimizations, i.e.,  sequentially using
each ``outcome`` as the optimization criterion.
No additional constraints should be specified for such selfish optimizations.
In other words, all constraints (including bounds on values of variables)
of the core model should reflect the logical, physical, economical, etc relations.
There should be no constraints representing preferences of the modeler.

Export of the model instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The model instance (in Pyomo called ``concrete model``) should be stored in
the ``dill``-format file.
Location and name of the file should be specified in configuration file of each
MCMA of this model.
The ``example.py`` model (included in the Template directory created during the ``pcmcma``
installation) includes a simple, reusable function performing this task.

Example of a core-model
^^^^^^^^^^^^^^^^^^^^^^^
The Template folder (created during ``pymcma`` installation) includes two
files illustrating the basic use of Pyomo for a core-model development,
as well as the model-instance export in the dill-format.
The example consists of two files:

#. ``example.py`` generates a very simple developed in Pyomo.
    Separate functions define the abstract model and the
    concrete model, respectively. The main function drives the model
    generation and exports the concrete model in the dill-format.

#. ``example.dat`` contains data in the AMPL format used in concrete model creation.
    In development of actual models other data formats might be more suitable.
    We suggest to consult the extensive Pyomo documentation for alternatives
    that might fit better management of data used for the core-model parameters.

The instance model object is exported to the dill-format file ``example.dll``.
The dill format is applied for serializing and de-serializing Python objects.
The ``example.dll`` file can be used as a core-model for MCMA with ``pymcma``
although the example is by far too simple for actual MCMA analysis.
For the latter we recommend to use the ``xpipa.dll`` demonstrated during the
installation testing.

Computation of the Pareto-front representation
----------------------------------------------
Usually one makes several analyses for one core-model.
The ``pymcma`` supports this practice by running each analysis in
the corresponding directory.
The examples discussed below illustrate how easy it can be to exploit
the offered functionality.

Overview
^^^^^^^^
Analysis of each core-model can be done in various ways.
Therefore, the below suggested steps is just an example.

#. Make sure that the ``pymcma`` conda environment is activated.
    Twe activation needs to be done only once in the terminal window, where the
    the analyses are made.
    To activate the environment execute:

    .. code-block:: console

        $ conda activate pymcma


#. Change to a dedicated analysis folder, further referred to as ``wdir``.
    The folder can be located anywhere in a file system in which the
    core-model is accessible.

#. In ``wdir`` create folder for first analysis, e.g., ``anaIni``.
    Typically, names of the analysis folders associated with the corresponding
    content of the analysis.
    We use the ``anaIni`` name for initial analysisl however, any other name can be used.
    For each subsequent analysis in ``wdir`` a distinct name should be specified.

#. Copy to ``anaIni`` a ``cfg.yml`` file.
    Advanced ``pymcma`` users might, of course, prefer to write the ``cfg.yml``
    file in ``anaInit``  directory from scratch.
    The ``cfg.yml`` file name should not be changed as it is used by ``pymcma``
    application.
    For initial analysis the configuration file ``cfg.yml`` provided in the
    Templates directory created upon installation might be a good start.

    The configuration file is specified in the YAML markup language but its
    modification can be done also without YAML's knowledge.
    It is enough to:

    - know that the # character denotes a comment line
    - refrain from modifications of the key-words (explained below)

    The provided ``cfg.yml`` is self-documented.
    Therefore, meanings of key-words are explained in the provided example.

#. Edit the copied ``cfg.yml`` to specify the configuration options described below.
    For initial analysis one can with explore analysis of the core-model with
    two criteria only.
    For subsequent analysis either other pairs of criteria can be specified or
    more criteria are usually defined.

    Note that the configuration files should be edited only with a text-editor.
    Any text editor (or programming tool) can be used for this purpose.

#. In ``wdir`` execute:

    .. code-block:: console

        $ pymcma --anaDir anaIni

    The command runs the ``pymcma`` for the analysis specified in the
    ``anaIni/cfg.yml`` file.

The steps 3 through 6 can be repeated with specifying different names of analysis
folders and specifying (in the corresponding ``cfg.yml`` file) different configuration
options.

Required configuration items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are only two required configuration options:

#. Core-model location and name
    This item is identified by the ``model_id`` key. Its argument defines the location
    (../Models/) of the model and the model name.
    The location can define either the relative or the absolute path to the directory
    containing the model.
    The model name (xpipa) is the root name of the dill-format file containing the
    core model.

#. Definition of criteria
    This item is identified by the ``crit_def`` key. Its argument defines the
    list of lists.
    Each of the internal list defines one criterion; it consists of three elements:

    #. Name of the criterion.
        The four criteria names of the example read: cost, carBal, water, grFuel.

    #. Criterion type: either ``min`` or ``max``.
        The first three criteria are minimized, the last is maxized.

    #. Name of the core model outcome variable defining the corresponding criterion.
        The four names of the core-model variables of the example read:
        cost, carbBal, water, greenFTot.


Below we show the two corresponding lines of the ``cfg.yml`` file defining the
required items:

.. code-block:: YAML

    model_id: ../Models/xpipa
    crit_def: [ [cost, min, cost], [carBal, min, carbBal], [water, min, water], [grFuel, max, greenFTot] ]

The above example shows how the corresponding entries look in the
``cfg.yml`` file of the test configuration.
Note that in this file almost all lines are commented,
i.e., have #-character as the first character of the line.

Note, that two commented lines in ``cfg.yml`` separate the necessary specs from optional
specs.
Only the two lines shown above are not commented in the necessary part.

The file also contains several other (all of these commented) criteria definitions
of the testing model ``xpipa`` installed with ``pymcma``.

Optional configuration items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Several run-time options can be activated by the corresponding configuration items,
which are located in the ``cfg.yml`` file below the marker:

.. code-block:: YAML

    # The following specs are optional.  --------------------------------------------

All but one these items are commented.
The only one not commented reads:

.. code-block:: YAML

    rep_vars: ['cost', 'carbBal', 'water', 'greenFTot', 'carb', 'carbCap', 'actS']

It defines the list of names of core-model variables, values of which are request to
be stored for each iteration.
The variables can be either scalar (i.e., not indexed) or indexed.
The values are stored in the Pandas data-frame and exported as the CSV-format file.
If the ``rep_vars`` are undefined (i.e., the corresponding line is commented) than
the file is not generated.

Note that values of each indexed variable is stored in the data-frame columns,
each column name is composed of the variable name and all pertaining combinations of
values of indices.
Therefore, for models with many such combinations the number of data-frame columns
will be large.
This should be taken into account in specification of the ``rep_vars`` list.

Each of the other optional items in the ``cfg.yml`` is composed of two commented lines.
The first contains the description of the option,
the second the name of the key-word with its default value.
The default value can be changed by uncommenting the second line and modifying the
default value.

Here are additional information on the meaning of the optional configuration items,
referred to by the corresponding key-word:

#.  ``resdir`` : name of the result sub-directory.
    The analysis results are stored in the analysis result subdirectory of
    the corresponding analysis directory.  For the above discussed analysis
    example it will be named ``anaIni/Results/``.
    The result sub-directory will be created by ``pymcma``.

#.  ``run_id`` : name of the additional sub-directory of the result sub-directory.
    It might be desired to store the results in a separate directory (e.g., for
    different configuration options).
    The additional sub-directory will be created by ``pymcma``.

#.  ``mxIter`` : maximum number of iterations.
    It might be desired to change the number of iteration for obtaining either
    faster an incomplete Pareto-front representation or continue to computations
    with a larger (than the default) iteration number.

#.  ``showPlot`` : to suppress showing the plots during the computations.
    If the computation time is too long to wait for seing the plots of the results,
    then showing the plots should be surpressed.
    Note that plots are always stored in the ``resdir``.


Results of analyses
-------------------
Results of each analysis are stored in the ``resdir`` directory.
New results overwrite the old-ones.
Therefore, in order to keep the old results one should define in the
``cfg.yml`` a new ``run_id``.

The stored results consist of Pandas data-frames and plots in the ``png`` format.
The data-frames are stored as the CSV-format files.
The column names of the data-frames are generated from the corresponding names
of either criteria or core-model variables.
Therefore, we recommend to use easy to associate names in the analysis and core-model
specification.

The result directory contains:

#. Data-frame with criteria values for each iteration.
    Each iteration is identified by its sequence-number.
    For each criterion and for each iteration criteria values are provided in
    two measurement units: (1) used in the core-model, and (2) nomarlized by the CAF
    (Criterion Achievement Function) to the common scale in which the largest/smallest
    value corresponds to the best/worst criterion performance within the Pareto-front.

#. Data-frame with values of the requested (in ``rep_vars``) core-model variables.
    The values for each iteration are exported to be available for problem/core-model
    specific analysis.
    To enable linking these values with the corresponding performance of the criteria,
    each iteration is identified by its sequence-number.
    The labels of the data-frame columns correspond to the variable names.
    The values of scalar (not indexed) variables are stored in one column.
    The values of each indexed variables are stored in separate columns;
    each column is labeled by the variable name and (sequentially generated)
    names corresponding to each comvination of values of indices.

#. Plots illustrating the Pareto front.
    Two plots are generated:

    - Two-dimensional sub-plots of all combinations of criteria pairs.
    - Parallel-coordinate plot of all criteria.

#. Plots illustrating computation progress.
    Two plots showing the state at each computation stage are generated:

    - Pair of plots showing numbers of iterations and of distinct solutions, respectively.
    - Distributions of distances between neighbor solutions.

Summary
-------
Complementary details on the core-model preparation and the analysis are available
in the companion paper submitted for publication in the SoftwareX journal.


Temporary notes (TO BE REMOVED)
-------------------------------

The PyMCMA software is configured and run based on a configuration file written in YAML markup language.

You can find the template configuration in TODO

Model name
^^^^^^^^^^

The first and most necessary thing is a definition of the model, which should be analyzed.
Models should be stored in ``.dll`` format in ``modDir`` (default is Models/) directory.

.. code-block:: YAML

    model_id: model_name


Criteria definition
^^^^^^^^^^^^^^^^^^^

This parameter defines criteria names and types. The value of this key is
composed of a list of lists (see example below). Each sub-list is composed of
three items. Each name of these items should be max. 8 characters long without spaces;
only the following characters are allowed: letters, _, and numbers.

Each list defines one criterion with three values:

#. Name of the criterion;
#. Criterion type: either ``min`` or ``max``;
#. Name of the core model outcome variable defining the corresponding criterion.

.. code-block:: YAML

    crit_def: [ [q1, max, x1], [q2, max, x2], [q3, max, x3] ]


Models directory
^^^^^^^^^^^^^^^^

The directory with models in ``.dll`` format.

.. code-block:: YAML

    modDir: Models/


Results directory
^^^^^^^^^^^^^^^^^

Directory in which all results will be stored. That includes DataFrames in ``.csv`` format
and visualizations in ``.png`` format.

.. code-block:: YAML

    resDir: Results/


Report configuration
^^^^^^^^^^^^^^^^^^^^

A list of core-model variables will be shown in the report.

.. code-block:: YAML

    rep_vars: ['cost', 'invT', 'carb', 'oilImp', 'capTot', 'actS']


Number of iterations
^^^^^^^^^^^^^^^^^^^^

The number of iterations to make. This variables define how many attempts to generate
Pareto representations will be done. Notice that the actual number of solutions
can be smaller because duplicated and close solutions are not included in the final set.

.. code-block:: YAML

    mxIter: 16


parRep
^^^^^^

TODO True for generating Pareto representation, False for predefined preferences.

.. code-block:: YAML

    parRep: True


Verbosity of report
^^^^^^^^^^^^^^^^^^^

Verbosity level of the analysis report. Possible values are in the range [0, 3].

.. code-block:: YAML

    verb: 0


Results' visualization
^^^^^^^^^^^^^^^^^^^^^^

Plots will be shown at the end of the analysis if ``True``. If set to ``False``, plots will be saved in ``resDir`` directory.

.. code-block:: YAML

    showPlot: True

Basic Usage
-----------

PyMCMA software runs based on the configuration written in YAML. Basic example
of the configuration file can be downloaded from ...TODO. Then, run the tool in
following way:

.. code-block:: console

   $ python -m pymcma user_cfg.yml

