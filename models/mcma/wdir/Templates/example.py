# Simple Pyomo model to demonstrate export of concrete model in the dill-format

import sys		# needed for stdout and sys.exit()
from os import R_OK, access
from os.path import isfile
import dill
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
from ex_inst import ex_inst  # model instance provider


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    m_name = 'example'     # model name (used for the dll-format file-name)
    # files
    m_data = 'example'    # data for defining the model instance

    # export model
    ex_inst(m_name, m_data)

    print(f'Model instance generated and dill-dumpped to: {m_name}')

