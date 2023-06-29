WARNING: the model is under development, not ready yet for actual use.
Comments are welcome, preferably in the repo Discussions or Issues.

Prototype of modular MCMA (Multiple-criteria Model Analysis) designed and
implemented to be linked with diverse, each separately developed, core
(substantive) models.
Both linked submodels, developed in Pyomo, are linked using the Pyomo
block-functionality.

In practice, substantive models are developed in two stages:
- SMS (Symbolic Model Specification) as pe.AbstractModel().
- model instance derived from the SMS with a corresponding selected data,
  generated as the pe.ConcreteModel() object.

Example of a simple Pyomo concrete model is available in t4conc.py, and
is used for initial testing of mcma.
Because of t4conc model simplicity, it is generated as concrete model
with embedded data defining values of parameters, i.e., without prior
generation of abstract model.

After basic mcma functionality will be implemented, the Pipa model will be
used first for extensive testing, and next mcma will be applied to actual
analysis of the Pipa model.
Actually, then use of mcma to MCMA of any LP model should be straightforward.
MCMA of convex non-linear models shall then be explored.

Details of the current MCMA implementation are in Notes.txt 
