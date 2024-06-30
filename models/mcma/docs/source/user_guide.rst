User Guide
==========
The ``pymcma`` package seamlessly integrates the Multiple-Criteria Model
Analysis (MCMA) with independently developed substantive models, and
autonomously computes Pareto-front representation composed of efficient
solutions that are uniformly distributed in terms of distances between neighbor
solutions. The ``pymcma`` illustrates the Pareto-front, also for more than
three criteria, and optionally exports the results for problems-specific
analysis in the substantive model's
variables space.

Overview of ``pymcma``
----------------------
Every Multiple-Criteria Model Analysis (MCMA) consists of two linked but
distinct tasks:

#. Development of a core model (aka substantive model)
    The model defines the relations between variables representing the criteria
    and all other variables (representing e.g., decisions, system state, etc).
    Discussion on methodology and tools for model development is beyond the
    ``pcmcma`` scope. Therefore, we present only the guidelines specific for
    model preparation to the MCMA.

#. Computations of the Pareto-front representation.
    Each Pareto solution fits best the specified preferences.
    In interactive MCMA the preferences are specified by the users.
    The ``pcmcma`` generates preferences autonomously aiming at sequentially
    decreasing the maximum distance between neighbor solutions in order to provide
    a uniformly distributed representation of the Pareto-front.
    Therefore, the MCMA part is for ``pymcma`` users very easy;
    it requires only a configuration of the desired analysis.

Below we discuss the requirements for each of the above two tasks.
The ``pymcma`` supports seamless integration of these two tasks, which makes
the objective (i.e., preference free) MCMA analysis very easy.

Issues common for both tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Both tasks should be done in the terminal windows with the activated conda
environment created during the ``pymcma`` installation.
From the user point of view, the linkage between these tasks consists of
only specification of two items in the analysis configuration file.
Therefore, the model development and its analysis can be done in
different folders; actually, it also can be done on different computers,
possibly running different OSs.

Development of the core model
-----------------------------
The ``pymcma`` will process any model developed according to the good modeling
practice provided it conforms to the additional requirements specified below.
All, but the first one, these requirements are typical for the MCMA tools and
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
More information on, and downloads of, Pyomo are available at Pyomo site:
http://www.pyomo.org .

In particular, ``pymcma`` provides seamless integration with the core-model,
also, if it is developed on another computer, possibly under a different
operating system.
Pyomo provides this critically important feature.
Namely, two independently developed Pyomo concrete models can be
included as blocks into a new concrete model.
Such integration preserves name-spaces; therefore, there are no naming
conflicts, typical for other model-instance integration methods,
e.g., merging the MPS-files.
Outline of the ``pymcma`` architecture is available in the corresponding
article.

Variables representing criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
At least two core-model variables should be defined to be used as criteria.
Further on such variables are called ``outcome variables`` or (for short)
``outcomes``.
Such variables have to be scalar (i.e., not indexed) and have names conforming
to the traditional naming requirements:

#. composed of only Latin letters and (optionally) digits, and
#. be maximum eight characters long.

One can define many ``outcomes``.
Actually, criteria are defined for each analysis; therefore, any core-model
variable conforming to the above requirements can serve as a criterion.
However, all variables intended to become criteria should be included in
the model testing.

Model testing
^^^^^^^^^^^^^
Before applying MCMA each model should pass comprehensive testing conforming
to the good modeling practice.
Testing should include single-criterion optimizations, i.e., sequentially using
each ``outcome`` as the optimization criterion.
No additional constraints should be specified for such selfish optimizations.
In other words, all constraints (including bounds on values of variables)
of the core model should represent only the logical, physical, economical, or other
relations.
In particular, there should be no constraints representing preferences of the modeler.

Export of the model instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The model instance (in Pyomo called ``concrete model``) should be stored in
the ``dill``-format file.
Location and name of the file should be specified in configuration file of each
``pymcma`` analysis of this model.
The next section discusses an example of the model generation and export.

Example of a core-model generation and export
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``Template/`` folder (created by running the ``pymcma --install`` command)
includes two files illustrating the basic use of Pyomo for
a core-model development, as well as the model-instance export in the ``dill``-format
accepted by the ``pymcma``.
The example consists of two files:

#. ``example.py`` - generates a very simple model developed in Pyomo.
    Separate functions define the abstract model and the
    concrete model, respectively. The main function drives the model
    generation and exports the concrete model in the dill-format.

#. ``example.dat`` - contains data in the AMPL format used in concrete model creation.
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
    The activation needs to be done only once in the terminal window, where
    the analyses are made.
    To activate the environment execute:

    .. code-block:: console

        $ conda activate pymcma


#. Change to a dedicated analysis folder, further referred to as ``wdir``.
    The folder can be located anywhere in a filesystem in which the
    core-model is accessible.

#. In ``wdir`` create folder for first analysis, e.g., ``anaIni``.
    Typically, names of the analysis folders associated with the corresponding
    content of the analysis.
    We use the ``anaIni`` name for initial analysis; however, any other name can be used.
    For each subsequent analysis in ``wdir`` a distinct name of the corresponding
    analysis folder should be chosen.

#. Copy a ``cfg.yml`` file to ``anaIni`` directory.
    The ``cfg.yml`` file name should not be changed as it is used by ``pymcma``
    application.
    For initial analysis the configuration file ``cfg.yml`` provided in the
    ``Templates`` directory created upon installation might be a good start.
    Advanced ``pymcma`` users might, of course, prefer to write the ``cfg.yml``
    file in each analysis directory from scratch.

    The configuration file is specified in the YAML markup language but its
    modification can be done also without YAML's knowledge.
    It is enough to:

    - know that the # character denotes a comment line
    - refrain from modifications of the key-words (explained below)

    The provided ``cfg.yml`` is self-documented.
    Therefore, meanings of keywords are explained in the provided example.

#. Edit the ``cfg.yml`` to specify the configuration options described below.
    For initial analysis one can explore analysis of the core-model with
    two criteria only.
    For subsequent analysis either other pairs of criteria can be specified or
    more criteria are usually defined.

    Note that the configuration files should be edited only with a text editor.
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
    (in the example it reads: ``../Models/``) of the model and the model name
    (in the example: ``xpipa``).
    The location can define either a relative or an absolute path to the directory
    containing the model.
    The model name is the root name of the dill-format file containing the
    core model (i.e., the specified name does not include the ``.dll`` extension).

#. Definition of criteria
    This item is identified by the ``crit_def`` key. Its argument defines the
    list of lists.
    Each of the internal list defines one criterion, which consists of three elements:

    #. Name of the criterion.
        The four criteria names of the example read: cost, carBal, water, grFuel.

    #. Criterion type: either ``min`` or ``max``.
        The first three criteria are minimized, the last is maximized.

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
The file also contains several other (all of these commented) criteria definitions
of the testing model ``xpipa`` installed with ``pymcma``.

Note, that the two commented lines in ``cfg.yml`` separate the necessary specs
from optional specs.
Only the two lines shown above are not commented in the necessary part.

In the ``cfg.yml`` file almost all lines are commented,
i.e., have #-character as the first character of the line.
This is done for providing:

    - self-documentation of the option-keys available for the users,

    - values of the corresponding default values of the option.


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

It defines the list of names of the core-model variables, values of which are
requested to be stored for each iteration.
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

#.  ``resdir`` - name of the result sub-directory.
    The analysis results are stored in the analysis result subdirectory of
    the corresponding analysis directory.  For the above discussed analysis
    example it will be named ``anaIni/Results/``.
    The result sub-directory will be created by ``pymcma``.

#.  ``run_id`` - name of the additional sub-directory of the result sub-directory.
    It might be desired to store the results in a separate directory (e.g., for
    different configuration options).
    The additional sub-directory (below the ``resdir``) will be created by
    specification of its name in the ``run_id`` option).

#.  ``mxIter`` - maximum number of iterations.
    It might be desired to change the number of iteration for obtaining either
    faster an incomplete Pareto-front representation or continue to computations
    with a larger (than the default) iteration number.

#.  ``showPlot`` - to suppress showing the plots during the computations.
    If the computation time is too long to wait for seeing the plots of the results,
    then showing the plots should be suppressed.
    Note that plots are always stored in the ``resdir``.


Results of analyses
-------------------
Results of each analysis are stored in the ``resdir`` directory.
New results overwrite the old ones.
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
    two measurement units: (1) used in the core-model, and (2) normalized by the CAF
    (Criterion Achievement Function) to the common scale in which the largest/smallest
    value corresponds to the best/worst criterion performance within the Pareto-front.

#. Data-frame with values of the requested (in ``rep_vars``) core-model variables.
    The values for each iteration are exported to be available for problem/core-model
    specific analysis.
    To enable linking these values with the corresponding performance of the criteria,
    each iteration is identified by its sequence-number.
    The labels of the data-frame columns correspond to the variable names.
    The values of scalar (not indexed) variables are stored in one column.
    The values of each indexed variable are stored in separate columns;
    each column is labeled by the variable name and (sequentially generated)
    names corresponding to each combination of the values of the indices.

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

