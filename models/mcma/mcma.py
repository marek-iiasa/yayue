""" Main function of the mcma: configure the analysis options and work-space. """

# infinity = float('inf')
# from os import R_OK, access
# from os.path import isfile
import sys		# needed for sys.exit()
import os
import argparse
import shutil
from datetime import datetime as dt
# from datetime import timedelta as td

from .cfg import Config  # configuration (dir/file location, parameter values, etc
from .driver import driver  # driver (run the analysis set-up and iterations)

SCRIPT_DIR = os.path.dirname(__file__)


def read_args():
    descr = """
    Compute uniformly distributed Pareto-front for specified criteria of the provided core-model.

    Examples of usage:
    python mcma.py -h
    python mcma.py --install
    python mcma.py --anaDir analysis_folder
    """

    parser = argparse.ArgumentParser(
        description=descr, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # noinspection SpellCheckingInspection
    instal = "--install : \n    install folders with templates."
    anaDir = "--anaDir string :\n    define analysis directory."
    parser.add_argument("--install", action="store_true", help=instal)  # on/off flag
    parser.add_argument("--anaDir", help=anaDir)

    # parse cli
    cl_args = parser.parse_args()
    return cl_args


# noinspection SpellCheckingInspection
def create_wdir():
    print('Creating directories with templates/examples.')

    dirs_to_create = ['Models', 'Templates', 'anaTst']

    found = False
    for adir in dirs_to_create:
        if os.path.exists(adir):
            print(f'\t"{adir}" directory exists; please remove it before running --install.')
            found = True
    if found:
        exit(1)

    orig_wdir = os.path.join(SCRIPT_DIR, 'wdir')
    for item in os.listdir(orig_wdir):
        s = os.path.join(orig_wdir, item)
        d = os.path.join('.', item)
        print(s, d)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy(s, d)



# noinspection SpellCheckingInspection
def main():
    version = '2.0.0'
    print(f'pyMCMA ver. {version}')
    tstart = dt.now()
    # print('Started at:', str(tstart))

    module_dir = 'mcma'         # needs to be changed (in the pymcma repo) to pymcma
    module_py = 'driver.py'
    as_module = os.path.exists(f'{module_dir}/{module_py}')  # true, if run as module, false if as pymcma
    if as_module:
        os.chdir(module_dir)
        print(f'Current working directory changed to "./{module_dir}".')
    args = read_args()
    # ana_dir = args.ana_id or 'anaTst'
    install = args.install
    ana_dir = args.anaDir
    if install:     # check, if wdir (composed of pymcma's templates and tests) should be installed
        assert ana_dir is None, 'ERROR: no analysis directory should be defined with the --install option.'
        create_wdir()
        exit(0)
    else:
        assert ana_dir is not None, 'ERROR: analysis directory should be defined.'
    print(f'Analysis directory: {ana_dir}')
    assert os.path.exists(ana_dir), f'The analysis directory "{ana_dir}" does not exist.'
    os.chdir(ana_dir)   # analysis run in the choosen/dedicated directory

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

    driver(cfg)  # driver and all needed objects of classes get all needed params from the cfg dict

    tend = dt.now()
    print('\nStarted at: ', str(tstart))
    print('Finished at:', str(tend))
    time_diff = tend - tstart
    # Format timedelta as hours:minutes:seconds
    hours, remainder = divmod(time_diff.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    # Display in HH:MM:SS format
    formatted_time = f'Wall-clock execution time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}'
    print(f'Wall-clock execution time: {time_diff.seconds} sec.')
    print(formatted_time)  # Output: 01:01:01


    if redir_stdo:  # close the redirected output
        f_out.close()
        sys.stdout = default_stdout
        print(f'\nRedirected stdout stored in {fn_out}. Now writing to the console.')
        print('\nStarted at: ', str(tstart))
        print('Finished at:', str(tend))
        print(f'Wall-clock execution time: {time_diff.seconds} sec.')


if __name__ == '__main__':
    main()
