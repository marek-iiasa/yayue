"""
Matouqin model main function
"""
import sys
import os
from datetime import datetime as dt
# from datetime import timedelta as td
from driver import driver  # driver (run the analysis set-up and iterations)


if __name__ == '__main__':
    tstart = dt.now()
    # print('Started at:', str(tstart))
    # wrk_dir = '.'  # might be modified by each user
    # os.chdir(wrk_dir)
    # print(f'wrk_dir: {wrk_dir}')
    out_dir = './Out_dir/'

    redir_stdo = False  # optional redirection of stdout to out_dir/stdout.txt
    default_stdout = sys.stdout
    if redir_stdo:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, mode=0o755)
        fn_out = out_dir + 'stdout.txt'  # file for redirected stdout
        print(f'Stdout redirected to: {fn_out}')
        f_out = open(fn_out, 'w')
        sys.stdout = f_out
    else:
        fn_out = None
        f_out = None

    driver()    # run generatation of parameters and their them for generating pe.ConcreteModel

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
