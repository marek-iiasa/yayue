# infinity = float('inf')

""" Main function of the mcma: import the core model, define the work-space. """

# todo: check consistency of using scaled and not-scaled entities
# todo: add/print info:
#   A/R undefined for Pareto set corners (virtual solutions, i.e., no values of model variables)
#   size of cubes in scaled coordinates, values of A/R in native (model-vars) scales

# from os import R_OK, access
# from os.path import isfile
# import sys		# needed for sys.exit()
# import os
import argparse
import shutil
from datetime import datetime as dt
# from datetime import timedelta as td

from .cfg import *  # configuration (dir/file location, parameter values, etc
from .driver import *  # driver (run the analysis set-up and iterations)

SCRIPT_DIR = os.path.dirname(__file__)


def read_args():
    descr = """
    Computing uniformly distributed Pareto-front for specified criteria of provided model.

    Examples of usage:
    python mcma.py -h
    python mcma.py --install
    python mcma.py --anaDir iniTst
    """

    parser = argparse.ArgumentParser(
        description=descr, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # noinspection SpellCheckingInspection
    instal = "--install : \n    install pyMCMA and test it."
    anaDir = "--anaDir string :\n    define analysis directory."
    parser.add_argument("--install", action="store_true", help=instal)  # on/off flag
    parser.add_argument("--anaDir", help=anaDir)

    # parse cli
    cl_args = parser.parse_args()
    return cl_args


# noinspection SpellCheckingInspection
def create_wdir():
    print('Initializing new working directory.')

    dirs_to_create = ['Models', 'Templates', 'anaTst']

    for adir in dirs_to_create:
        os.mkdir(adir)

    files_to_copy = [
        'wdir/Models/xpipa.dll',
        'wdir/Templates/cfg.yml',
        'wdir/Templates/example.py',
        'wdir/Templates/example.dat',
        'wdir/anaTst/cfg.yml',
        ]

    for file in files_to_copy:
        shutil.copyfile(src=os.path.join(SCRIPT_DIR, file),
                        dst=file.removeprefix('wdir/'))


# noinspection SpellCheckingInspection
def main():
    # noinspection SpellCheckingInspection
    tstart = dt.now()
    # print('Started at:', str(tstart))

    # wdir = '.'     # current dir is the wdir for both development and packaged version
    # assert os.path.exists(wdir), f'The work directory "{wdir}" does not exist'
    # os.chdir(wdir)
    # process cmd-line args (currently only either install or ana_dir)
    module_dir = 'mcma'
    as_module = os.path.exists(module_dir)  # true, if run as module
    if as_module:
        os.chdir(module_dir)
        print(f'Current working directory changed to ./{module_dir}')
    args = read_args()
    # ana_dir = args.ana_id or 'anaTst'
    install = args.install
    ana_dir = args.anaDir
    if install:
        assert ana_dir is None, f'ERROR: no directory should be defined for the installation.'
        ana_dir = 'anaTst'
        if as_module:
            print('Skip installation of test directories in the development mode.')
        else:
            print('Installing test directories.')
            create_wdir()
    else:
        assert ana_dir is not None, f'ERROR: analysis directory should be defined.'
    print(f'Analysis directory: {ana_dir}')
    assert os.path.exists(ana_dir), f'The analysis directory "{ana_dir}" does not exist'
    os.chdir(ana_dir)

    # process the run configuration options and configure the working space
    config = Config()    # process yaml config. file
    cfg = config.data   # dict with config. options
    if cfg.get('verb') > 1:
        print(f'Configuration options after processing:\n\t{cfg}')

    # optional standard output redirection
    default_stdout = sys.stdout
    fn_name = cfg.get('fn_out')  # file-name for redirected stdout
    if fn_name is None:
        redir_stdo = False  # no redirection of stdout to a file
        fn_out = None
        f_out = None
    else:
        redir_stdo = True  # optional redirection of stdout to the stdOut file
        fn_out = f'{cfg.get("resDir")}{fn_name}'  # path to the file for redirected stdout
        # assert not os.path.exists(fn_out), f'Rename/remove the already used file: {fn_out}'
        print(f'Stdout redirected to: "{fn_out}".')
        f_out = open(fn_out, 'w')
        sys.stdout = f_out

    driver(cfg)  # driver and all classes get all needed info from the cfg dict

    tend = dt.now()
    print('\nStarted at: ', str(tstart))
    print('Finished at:', str(tend))
    time_diff = tend - tstart
    print(f'Wall-clock execution time: {time_diff.seconds} sec.')

    if redir_stdo:  # close the redirected output
        f_out.close()
        sys.stdout = default_stdout
        print(f'\nRedirected stdout stored in {fn_out}. Now writing to the console.')
        print('\nStarted at: ', str(tstart))
        print('Finished at:', str(tend))
        print(f'Wall-clock execution time: {time_diff.seconds} sec.')


if __name__ == '__main__':
    main()
