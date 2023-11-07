""" Configuration class """
import os.path
import yaml
from yaml.loader import SafeLoader
'''
import os
'''


class Config:
    def __init__(self, f_cfg):
        self.f_cfg = f_cfg    # full path to the yaml config file
        self.data = None      # config data read from the config file
        self.rd_cfg()
        print(self.data)
        # raise Exception('test stop')

    def rd_cfg(self):
        assert os.path.exists(self.f_cfg), f'YAML configuration file "{self.f_cfg}" is not readable.'
        with open(self.f_cfg) as f:
            self.data = yaml.load(f, Loader=SafeLoader)

