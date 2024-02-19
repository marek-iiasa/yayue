User Guide
==========
The pyMCMA .... (adapt from the paper)....

Working space
-------------
Overview the concept

Structured working env.

Explain (possibly many) wdirs (possibly duplicates of templates?)

Structure of the distributed wdir

Initial content of wdir

Overview of pyMCMA
------------------
Every Multiple-Criteria Model Analysis (MCMA) consists of two tasks:

#. Development of a core model (aka substantive model)
    The model defines the relations between variables representing the criteria
    and all other variables (representing e.g., decisions, system state, etc).

#. Computations of Pareto-efficient solutions
    Each of such solutions fits best the specified preferences.
    In interactive MCMA the preferences are specified by the users.
    The pyMCMA generates preferences autonomously aiming at sequentially decreasing
    the maximum distance between neighbor solutions in order to provide
    a uniformly distributed representation of the Pareto-front.

The pyMCMA seamlessly integrates these two tasks, which makes the objective
(i.e., preference free) MCMA analysis easy.
Below we discuss the requirements for each of the above two tasks.

Development of the core model
-----------------------------
The pyMCMA will process any model developed according to the good modeling
practice provided it conforms to the additional requirements specified below.
All but the first these requirements are typical for the MCMA tools and
are easy to conform to.

Modeling environment
^^^^^^^^^^^^^^^^^^^^
The pyMCMA can be integrated only with models developed in Pyomo,
the Python-based, open-source structured modeling language.
Pyomo is widely used, countless open-source models of diverse problems
are posted on the GitHub.
Actually, Pyomo provides a rich collection of classes, objects of which
provide building blocks for development of properly structured models.
Moreover, being Python-based, functionality of Pyomo can easily combined
with diverse Python-packages supporting wide range of various functionalities.
Therefore, the pyMCMA developers consider Pyomo as the best available
environment for development of algebraic models.
More information on, and downloads of Pyomo are available at www.pyomo.org

In particular, pyMCMA requires seamless integration with the core-model
developed on another computer, possibly under a different operating system.
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
However, all variables intented to become criteria should be included in
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
(to be written after export/import will work)

TODO Include in the working-space distribution an example (template) of export.

Multiple-Criteria Model Analysis (MCMA)
---------------------------------------
(to be written by adapting to the below structure the original draft by AS;
the draft is moved to the Temporary notes section below)

Overview
^^^^^^^^

Specification of the necessary items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Specification of the optional items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Running the computations
^^^^^^^^^^^^^^^^^^^^^^^^

Results of analyses
-------------------
(many diverse analyses), easy to structure (either by results-tree or by usr_id)

Temporary notes
---------------

The PyMCMA software is configured and run based on a configuration file written in YAML markup language.

You can find the template configuration in TODO

Model name
^^^^^^^^^^

The first and most necessary thing is a definition of the model, which should be analyzed. Models should be stored in
``.dll`` format in ``modDir`` (default is Models/) directory.

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

