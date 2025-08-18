""" Configuration class """
import os.path
import yaml
from yaml.loader import SafeLoader


# noinspection SpellCheckingInspection
class Config:
    def __init__(self):     # current wdir is the ana_dir; cfg.yml must be located here
        self.f_sys = './../Sys/cfg_sys.yml'    # full path to the system config file
        self.f_usr = './cfg.yml'    # usr config
        self.f_cfgLoc = './cfg.txt'    # alternative cfg-file location (optional)
        self.usrOptions = ''    # user-defined (read from self.f_user file) options
        self.data = None      # config data read from both Sys and usr config files
        self.cfgLoc()
        self.rd_cfg(self.f_sys)
        self.rd_cfg(self.f_usr)   # usr_cfg is in the current dir
        # print(f'Configuration options read:\n\t{self.data}')
        self.chk_dirs()       # check the needed dirs
        # raise Exception('test stop')

    def cfgLoc(self):       # use optional cfg-file location, if it is available
        fLoc = self.f_cfgLoc
        if not os.path.exists(fLoc):
            print(f'Optional cfg-file specs file "{fLoc}" not found. Using the default: "{self.f_usr}"')
            return
        if os.path.exists(self.f_usr):
            print(f'The cfg-file specs "{self.f_usr}" is ignored.')
            pass
        with open(fLoc, "r") as reader:
            print(f"\nReading the cfg-file location from file '{fLoc}':")
            for line in reader:     # only one line processed
                line = line.rstrip("\n")
                # print(f'line {line}') # noqa
                words = line.split()
                n_words = len(words)
                assert n_words == 1, f'line {line} has {n_words} instead of the required one.'
                fCfg = words[0]
                if os.path.exists(fCfg):
                    self.f_usr = fCfg
                    # print(f"The analysis cfg will be read from file '{fLoc}':")
                    return
                else:
                    raise FileNotFoundError(f"The specified cfg-file '{fCfg}' not found.")
        raise Exception(f"Empty file '{fLoc}'.")

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
                    self.usrOptions += f'\t{k}: {v}\n'
                print(f'User-defined cfg-options:\n{self.usrOptions}')

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
