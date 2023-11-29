import pyomo.environ as pe

m = pe.AbstractModel('Matouqin v. 0.1')

H_init = {}
H_init[2] = [1, 3, 5]
H_init[3] = [2, 4, 6]
H_init[4] = [3, 5, 7]
m.H = pe.Set([2, 3, 4], initialize=H_init)

print (f'H_init', H_init, 'H', m.H)