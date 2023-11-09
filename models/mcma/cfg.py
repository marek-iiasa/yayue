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
        self.chk_dirs()       # check the needed dirs
        # raise Exception('test stop')

    def rd_cfg(self):       # upload yaml config file
        assert os.path.exists(self.f_cfg), f'YAML configuration file "{self.f_cfg}" is not readable.'
        print(f'Processing yaml configuration file "{self.f_cfg}".')
        with open(self.f_cfg) as f:
            self.data = yaml.load(f, Loader=SafeLoader)

    def chk_dirs(self):       # check, if the needed dirs are writeable
        home = self.data.get('wrkDir')
        for d in ['modDir', 'resDir']:
            dir_name = f'{home}{self.data.get(d)}'
            if not os.path.exists(dir_name):
                os.makedirs(dir_name, mode=0o755)
                print(f'directory "{dir_name}" created')
