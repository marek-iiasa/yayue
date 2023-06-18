WARNING: the model is under development, not ready yet for actual use.
Comments are welcome, preferably in the repo Discussions or Issues.

Prototype of modular MCMA (Multiple-criteria Model Analysis) submodel to be
linked with diverse, each separately developed, substantive submodels.
Both linked submodels, developed in Pyomo, are linked using the Pyomo
block-functionality.

In practice, substantive models are developed in two stages:
- SMS (Symbolic Model Specification) as pe.AbstractModel().
- model instance derived from the SMS with a corresponding selected data,
  generated as the pe.ConcreteModel() object.

Example of a simple Pyomo concrete model is available in t4conc.py.
