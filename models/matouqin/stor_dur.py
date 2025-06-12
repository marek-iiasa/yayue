"""
Prototype of storage time calculation
"""

import pandas as pd
from collections import deque


# get storage duration for each xIns
def stor_dur(res_dir, csv_file):
    sflow_df = pd.read_csv(f'{res_dir}{csv_file}', index_col=0)
    sflow_df[sflow_df < 1e-5] = 0  # reset 0
    sflow_df = sflow_df.round(2)
    sflow_df = sflow_df.loc[:, (sflow_df != 0).any(axis=0)]  # delete all zero cols

    xins_cols = [c for c in sflow_df.columns if c.startswith('xIns')]
    xouts_cols = [c for c in sflow_df.columns if c.startswith('xOuts')]

    # get storage device names, ESS_s
    s_names = set(c.replace('xIns_', '') for c in xins_cols) | set(c.replace('xOuts_', '') for c in xouts_cols)
    s_res = {
        'BESS_BAT': 0.99,
        'HESS_HT1': 1,
        'HESS_HT2': 1,
        'CAESS_CAT1': 1,
        'CAESS_CAT2': 1
    }

    # create dict to stor in/out info
    s_cols = {}
    for s in s_names:
        xins = f'xIns_{s}' if f'xIns_{s}' in sflow_df.columns else None
        xouts = f'xOuts_{s}' if f'xOuts_{s}' in sflow_df.columns else None
        s_cols[s] = {'xIns': xins, 'xOuts': xouts}

    # set que for each ESS
    que = {s: deque() for s in s_names}

    # record: ess, xins_time, xouts_time, duration, qty
    records = []

    # id for each xIns_t
    b_id = 0
    b_id_rel = set()    # energy release id

    # start cycling，first store, then release, FIFO, first in first out
    for idx, row in sflow_df.iterrows():
        t = idx

        # do self-discharge
        for s, dq in que.items():
            res = s_res.get(s, 1.0)
            for batch in dq:
                batch['qty'] = batch['qty'] * res
                if batch['qty'] < 1e-4:     # storage < 0.1 kWh, set storage == 0
                    batch['qty'] = 0.0

        for s, cols in s_cols.items():
            # stor
            if cols['xIns'] is not None:
                qty_in = row[cols['xIns']]
                if qty_in > 0:
                    que[s].append({
                        # 'qty': round(qty_in, 2),      # energy have not been released in queue
                        'qty': qty_in,
                        'time_in': t,       # xIns time
                        'batch_id': b_id,     # xIns id
                        'xIns': qty_in      # store xIns value
                    })
                    b_id += 1

            # release
            if cols['xOuts'] is not None:
                qty_out = row[cols['xOuts']]
                rel_need = qty_out      # energy needed release

                while rel_need > 0 and que[s]:
                    oldest = que[s][0]
                    stored_qty = oldest['qty']
                    time_in = oldest['time_in']
                    batch_id = oldest['batch_id']

                    time_out = t
                    duration = time_out - time_in

                    # record xIns value when it first in storage
                    if batch_id not in b_id_rel:
                        xins_val = oldest['xIns']
                        b_id_rel.add(batch_id)
                    else:
                        xins_val = 0

                    if stored_qty <= rel_need:
                        # xOuts > stored, fully release
                        records.append({
                            'storage': s,
                            'batch_id': batch_id,
                            'time_in': time_in,
                            'time_out': time_out,
                            'duration': duration,
                            'qty_rel': stored_qty,       # energy released from xIns_id
                            'xIns': xins_val,   # record xIns when it first in
                            'is_final_residual': False      # is xIns still stored
                        })
                        # remaining = round(remaining - stored_qty, 2)
                        rel_need = rel_need - stored_qty
                        que[s].popleft()        # delete the left
                    else:
                        # 0 < xOuts < xIns, xIns partly release, update new qty for xIns_t
                        records.append({
                            'storage': s,
                            'batch_id': batch_id,
                            'time_in': time_in,
                            'time_out': time_out,
                            'duration': duration,
                            'qty_rel': rel_need,       # xOuts from xIns_id
                            'xIns': xins_val,
                            'is_final_residual': False
                        })
                        # oldest['qty'] = round(oldest['qty'] - remaining, 2)
                        oldest['qty'] = oldest['qty'] - rel_need
                        rel_need = 0

                # if remaining > 0, but no xIns

    # records xIns vol which not release till the end
    final_time = sflow_df.index.max()
    for s, dq in que.items():
        for batch in dq:
            time_in = batch['time_in']
            qty_rem = batch['qty']
            batch_id = batch['batch_id']
            time_out = None
            duration = final_time - time_in
            records.append({
                'storage': s,
                'batch_id': batch_id,
                'time_in': time_in,
                'time_out': time_out,
                'duration': duration,
                'qty_rel': qty_rem,     # energy amount not released
                'xIns': 0,
                'is_final_residual': True   # energy not released
            })

    # convert to df
    s_state_df = pd.DataFrame.from_records(
        records, columns=['storage', 'batch_id', 'time_in', 'time_out', 'duration',
                          'qty_rel', 'xIns', 'is_final_residual']
    )
    s_state_df['qty_rel'] = s_state_df['qty_rel'].round(3)

    s_state_df.sort_values(['storage', 'time_in', 'batch_id'], inplace=True)
    s_state_df.reset_index(drop=True, inplace=True)     # reset index 0-N

    return s_state_df


# summary ESSs storage duration, max, min, mean
def sum_stor_dur(s_state_df):
    st_df = s_state_df

    end_t = st_df['time_in'].max()      # get the end time
    st_df = st_df[st_df['time_in'] != end_t].copy()        # exclude the xIns in the last time
    # exclude final residual == Ture, which xIns is used to fulfill xVol_end == xVol_init
    st_df = st_df[~st_df['is_final_residual']]

    # max duration time of each xins
    xins_dur = (
        st_df
        .groupby(['storage', 'batch_id'], as_index=False)
        .agg(
            time_in=('time_in', 'first'),
            duration=('duration', 'max')
        )
    )

    # print(f'Max = {xins_dur}')

    # max, min and mean duration time of ESSs
    ess_dur = (
        xins_dur
        .groupby('storage', as_index=True)
        .agg(
            max_dur=('duration', 'max'),
            min_dur=('duration', 'min'),
            avg_dur=('duration', 'mean'),
        )
        .assign(avg_dur=lambda df: df['avg_dur'].round(2))

    )

    # print(f'summary: {ess_dur}')

    return xins_dur, ess_dur


if __name__ == '__main__':
    ppath = '.'
    rep_dir = f'{ppath}/Results/0.2cost/'
    sflow_f = 'flow_s.csv'
    # sflow_f = 'sflowc.csv'    # 10 periods test.
    sdur_f = 'sDur.csv'
    df_dur = stor_dur(rep_dir, sflow_f)
    xins_d, ess_d = sum_stor_dur(df_dur)

    # print(df_dur.head(5))
    print(f'ESSs storage duration are {ess_d}')

    df_dur.to_csv(f'{rep_dir}{sdur_f}', index=False)
    xins_d.to_csv(f'{rep_dir}xins_dur.csv', index=False)
    print(f'\nStorage duration time are stored in {rep_dir}{sdur_f} and {rep_dir}xins_dur.csv.')
