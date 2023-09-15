This repo contains a simple clustering app and the set of data.
The data, stored in alter121.csv was developed in 2019 by Tieju Ma, Hongtao Ren,
and Binqqing Ding, ECUST Shanghai by analysis of a dedicated model of technology
learning.
The data represents values of several criteria for each considered considered
alternative. Each alternative is defined by a combination of technology learning
rates of two technologies; there are 11 considered rates for each technology;
thus, 121 alternatives were defined.
Most of such alternatives are dominated by another alternatives, i.e., are Pareto
inefficient.
An auxiliary application was developed to filter all 121 alternatives the subset
of Pareto alternatives.
Information about the Pareto alternative sets is stored in pareto.csv.
Note, that the Pareto sets differ for diverse combinations of the considered criteria.

The original applications and the detailed analysis results were developed by
Hongtao Ren of ECUST, and Marek Makowski of IIASA.
The original code was developed in Nov. 2019 in Jupyter notebook; final
explorations were done in Jan. 2021 in techn-dir.
These are stored in dedicated repo, i.e., ~/ime/pubs/19techn/data3/stats.
This repo also contains the code for generation of 4K MCAA (Multiple-Criteria
Analysis of Alternatives) representing all possible combinations of preferences
(specified as relative criteria importance).
In techn sub-dir exploration results involving additional risk-criteria (for MCMA
study) are stored.
In sa_itr sub-dir exploration results of the Saudi-Arabia case are stored.

The clustering code was developed by Marek Makowski, IIASA.
The code of 2020 was refactorized in order to improve the readability and conform
to the recommend style of the Python code.

The current code can be easily (by commenting/un-commenting the corresponding
statements) modified for diverse analysis (in particular, of specific criteria
combinations and/or cluster numbers) of the provided set of alternatives.
