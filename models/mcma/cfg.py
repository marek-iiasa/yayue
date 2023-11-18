""" Configuration class """
import os.path
import yaml
from yaml.loader import SafeLoader


class Config:
    def __init__(self, ana_def):
        self.f_sys = './Sys/cfg_sys.yml'    # full path to the system config file
        self.ana_def = ana_def    # full path to the user yaml config file
        self.rel_ana_dir = None    # relative (to ./Data) path to the user analysis dir
        self.data = None      # config data read from both Sys and usr config files
        self.rd_cfg(self.f_sys)
        self.rd_cfg(self.ana_def)
        # print(f'Configuration options read:\n\t{self.data}')
        self.chk_dirs()       # check the needed dirs
        print(f'Configuration options after processing:\n\t{self.data}')
        # raise Exception('test stop')

    def rd_cfg(self, f_name):       # upload yaml config file
        if f_name == self.f_sys:
            cfg_id = 'sys_config'
            sys_data = True
        else:
            cfg_id = 'usr_config'
            sys_data = False
            assert os.path.exists(f_name), f'analysis config file "{f_name}" is not readable.'
            with open(f_name) as f:   # get the ana_dir name
                dir_def = yaml.load(f, Loader=SafeLoader)
            rel_ana_dir = dir_def.get("ana_dir")
            assert rel_ana_dir is not None, f'Undefined key "ana_dir" in user config. file "{f_name}".'
            self.rel_ana_dir = rel_ana_dir
            f_name = f'./Data/{rel_ana_dir}cfg_usr.yml'  # full path to cfg_usr file
        print(f'Processing yaml "{cfg_id}" file "{f_name}".')
        with open(f_name) as f:
            if sys_data:
                self.data = yaml.load(f, Loader=SafeLoader)
            else:
                usr_data = yaml.load(f, Loader=SafeLoader)
                for k, v in usr_data.items():   # add or over-write options by options defined in cfg_usr
                    self.data.update({k: v})

    def chk_dirs(self):       # check, if the needed dirs are writeable, create those necessary
        home_root = self.data.get('wrkDir')
        if home_root != './':
            assert os.path.exists(home_root), f'Working directory {home_root} does not exists.'
            os.chdir(home_root)
            print(f'Home (MCMA working dir) changed to: "{home_root}".')
        mod_dir = f'{home_root}{self.data.get("modDir")}'
        assert os.path.exists(mod_dir), f'Model directory "{mod_dir}" does not exist.'
        ana_dir = f'{home_root}Data/{self.rel_ana_dir}'  # full path the usr-defined ana_dir
        self.data.update({'ana_dir': ana_dir})
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
