""" Configuration class """
import os.path
import yaml
from yaml.loader import SafeLoader


# noinspection SpellCheckingInspection
class Config:
    def __init__(self):     # current wdir is the ana_dir; cfg.yml must be located here
        self.f_sys = './../Sys/cfg_sys.yml'    # full path to the system config file
        self.f_usr = './cfg.yml'    # usr config
        self.data = None      # config data read from both Sys and usr config files
        self.rd_cfg(self.f_sys)
        self.rd_cfg(self.f_usr)   # usr_cfg is in the current dir
        # print(f'Configuration options read:\n\t{self.data}')
        self.chk_dirs()       # check the needed dirs
        # raise Exception('test stop')

    def rd_cfg(self, f_name):       # upload yaml config file
        if f_name == self.f_sys:
            # assert os.path.exists(f_name), f'system config file "{f_name}" is not readable.'
            if not os.path.exists(f_name):
                self.sys_default()  # if cfg_sys not accessible, then set the defaults
                return
            cfg_id = 'sys_config'
            sys_data = True
        else:
            cfg_id = 'usr_config'
            sys_data = False
            assert os.path.exists(f_name), f'analysis user-config file "{f_name}" is not readable.'
        print(f'Processing yaml "{cfg_id}" file "{f_name}".')
        with open(f_name) as f:
            if sys_data:
                self.data = yaml.load(f, Loader=SafeLoader)
            else:
                usr_data = yaml.load(f, Loader=SafeLoader)
                for k, v in usr_data.items():   # add or over-write options by options defined in cfg_usr
                    self.data.update({k: v})

    def sys_default(self):       # set default values of Sys/cfg
        sysDefaults = {'resDir': 'Results/', 'mxIter': 1000, 'showPlot': True, 'neutral': True, 'verb': 0}
        self.data = {}
        for k, v in sysDefaults.items():  # set default values
            self.data.update({k: v})

    def chk_dirs(self):       # check, if the needed dirs are writeable, create those necessary
        res_dir = f'./{self.data.get("resDir")}'
        if not os.path.exists(res_dir):
            os.makedirs(res_dir, mode=0o755)
            print(f'directory "{res_dir}" created for storing results of analysis.')
        sub_dir = self.data.get('run_id')
        if sub_dir is not None:
            sub_dir = f'{res_dir}{sub_dir}'
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir, mode=0o755)
                print(f'dedicated subdirectory "{sub_dir}" created for storing results.')
            res_dir = sub_dir
        self.data.update({'resDir': res_dir})
        print(f'Results (dfs and plots) will be stored in "{res_dir}".')
