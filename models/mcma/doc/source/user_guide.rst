User Guide
==========

Creating own model
------------------

Configuration file
------------------

The PyMCMA software is configured and run based on a configuration file written in YAML markup language.

You can find the template configuration in TODO


Model name
^^^^^^^^^^

The first and most necessary thing is a definition of the model which should be analysed. Models should be stored in
``.dll`` format in ``modDir`` (default is Models/) directory.

.. code-block:: YAML

    model_id: model_name


Criteria definition
^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

    crit_def: [ [q1, max, x1], [q2, max, x2], [q3, max, x3] ]


Models directory
^^^^^^^^^^^^^^^^

.. code-block:: YAML

    modDir: Models/


Results directory
^^^^^^^^^^^^^^^^^

.. code-block:: YAML

    resDir: Results/


Report configuration
^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

    rep_vars: ['cost', 'invT', 'carb', 'oilImp', 'capTot', 'actS']


Number of iterations
^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

    mxIter: 16


parRep
^^^^^^

.. code-block:: YAML

    parRep: True


Verbosity of report
^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

    verb: 0


Results' visualization
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

    showPlot: True