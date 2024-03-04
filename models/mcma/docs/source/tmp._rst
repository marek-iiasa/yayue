
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


