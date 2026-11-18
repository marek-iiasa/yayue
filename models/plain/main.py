# Simple Pyomo model to demonstrate export of concrete model in the dill-format

from ex_inst import ex_inst  # model instance provider
'''
import sys		# needed for stdout and sys.exit()
from os import R_OK, access
from os.path import isfile
import dill
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
'''

# noinspection SpellCheckingInspection
def main():
    m_name = 'plain'     # model name (used for the dll-format file-name)
    # files
    m_data = 'jg1'    # data for defining the model instance

    # export model
    ex_inst(m_name, m_data)

    # print(f'Model instance generated and dill-dumped to: {m_name}')

if __name__ == '__main__':
    main()
