"""
Report writer
"""
# import os.path

# import sys		# needed for sys.exit()
# import os
# import pandas as pd
import pyomo.environ as pe  # needed for extracting elements of the solution


def report(m):

    # print(f'\nPlace holder for report results of model {m.name}.')
    # revenue = f'{pe.value(model.revenue):.3e}'      # scientific counting method, accurate to three decimal places

    print('\nValues of decision variables ----------------------------------------------------------------------------')
    # print(f'Total storage capacity = {pe.value(m.sCap)} MW')
    # print(f'Numbers of storage devices = {pe.value(m.sNum)}')

    print('\nValues of outcome variables -----------------------------------------------------------------------------')
    print(f'Total revenue  = {pe.value(m.revenue)} million RMB')
    print(f'Income  = {pe.value(m.income)} million RMB')
    print(f'Investment cost  = {pe.value(m.invCost)} million RMB')
    print(f'Operation and maintenance cost  = {pe.value(m.OMC)} million RMB')
    print(f'Surplus cost  = {pe.value(m.overCost)} million RMB')
    print(f'Shortage cost  = {pe.value(m.buyCost)} million RMB')
    print(f'Balance cost  = {pe.value(m.balCost)} million RMB')
