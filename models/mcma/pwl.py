"""
Handling of the CAF-PWL
"""


class PWL:  # representation of caf(x)
    def __init__(self, cr):  # cr: specs of a criterion
        self.cr_name = cr.name
        self.mult = cr.mult  # 1 for max-crit, -1 for min.
        self.utopia = cr.utopia
        self.asp = cr.asp
        self.res = cr.res
        self.nadir = cr.nadir
        self.vert_x = []    # x-values of vertices
        self.vert_y = []    # y-values of vertices
        print(f"PWL initialized: cr_name = '{self.cr_name}', mult = '{self.mult}', U = '{self.utopia}', "
              "A = '{self.asp}', R = '{self.res}', R = '{self.nadir}'.")
