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
        print(f'Configuration options read:\n\t{self.data}')
        self.chk_dirs()       # check the needed dirs
        print(f'Configuration options after processing:\n\t{self.data}')
        # raise Exception('test stop')

    def rd_cfg(self):       # upload yaml config file
        assert os.path.exists(self.f_cfg), f'YAML configuration file "{self.f_cfg}" is not readable.'
        print(f'Processing yaml configuration file "{self.f_cfg}".')
        with open(self.f_cfg) as f:
            self.data = yaml.load(f, Loader=SafeLoader)

    def chk_dirs(self):       # check, if the needed dirs are writeable
        home_root = self.data.get('wrkDir')
        if home_root != './':
            assert os.path.exists(home_root), f'Working directory {home_root} does not exists.'
            os.chdir(home_root)
            print(f'Home (MCMA working dir) changed to: "{home_root}".')
        mod_dir = f'{home_root}{self.data.get("modDir")}'
        assert os.path.exists(mod_dir), f'Model directory "{mod_dir}" does not exist.'
        ana_dir = f'{home_root}{self.data.get("ana_dir")}'
        assert os.path.exists(ana_dir), f'Analysis home directory "{ana_dir}" does not exist.'
        print(f'MCMA analysis directory: "{ana_dir}".')
        res_dir = f'{ana_dir}{self.data.get("resDir")}'
        if not os.path.exists(res_dir):
            os.makedirs(res_dir, mode=0o755)
            print(f'directory "{res_dir}" created for storing results.')
        sub_dir = self.data.get('run_id')
        if sub_dir is not None:
            sub_dir = f'{res_dir}{sub_dir}'
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir, mode=0o755)
                print(f'dedicated subdirectory "{sub_dir}" created for storing results.')
            res_dir = sub_dir
        self.data.update({'resDir': res_dir})
        print(f'Results (dfs and plots) will be stored in "{res_dir}".')
