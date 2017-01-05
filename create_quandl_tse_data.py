# -*- coding: utf-8 -*-
"""
* unit32 以上の volume は upper bound clip

"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import tqdm


QUANDL_DIR = "data/input"
QUANDL_TEMP = os.path.join(QUANDL_DIR, "quandl-xjpx.h5")
QUANDL_RAW = os.path.join(QUANDL_DIR, "XJPX.zip")
QUANDL_CODE = os.path.join(QUANDL_DIR, "")
QUANDL_KEY = "xjpx"
QUANDL_XJPX_COLS = [
    "ecode",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adj_factor",
    "adj_type",
]
MAX_VOL = 2 ** 32 - 1
SYMBOLS = pd.read_csv(
    os.path.join(QUANDL_DIR, "quandl-xjpx.ecodes.topix500.csv")
).ecode.astype(str).tolist()


def preprocessing():
    df = pd.read_csv(
        QUANDL_RAW,
        compression='zip',
        names=QUANDL_XJPX_COLS)
    # df.to_hdf(QUANDL_TEMP, 'orig', complib='blosc', complevel=9)
    df.loc[:, 'n_elems'] = df.ecode.apply(lambda x: len(x.split('_')))
    df = df[(df.ecode.str.endswith('_UADJ')) & (df.n_elems == 2)]
    df.drop('n_elems', axis=1, inplace=True)

    print(len(df[df['volume'] > MAX_VOL]))
    df.loc[:, 'ecode'] = df.ecode.str[:-5]
    df.loc[:, 'volume'] = df.volume.clip(0, MAX_VOL)
    df.ecode.astype(int, inplace=True)
    df = df[df.ecode.isin(SYMBOLS)]
    df.to_hdf(QUANDL_TEMP, QUANDL_KEY, complib='blosc', complevel=9)


def preproc_split():
    df = pd.read_hdf(QUANDL_TEMP, QUANDL_KEY)
    # df = df[df.ecode.isin(SYMBOLS)].dropna(subset=['adj_type'])
    df = df[df.ecode.isin(SYMBOLS)]
    df.loc[:, 'date'] = pd.to_datetime(df.date)
    df.loc[:, 'date_shift'] = df.date.shift(1)
    df.dropna(inplace=True)

    # fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    # ax.plot(df.date, df.adj_factor)
    # plt.savefig('adj.png')
    df.set_index('date_shift', inplace=True)
    df.index.name = 'effective_date'
    df = df[
        (df.adj_type == 6.0) &
        (df.adj_factor != 1.0)
    ]
    df = df.rename(columns={
        'adj_factor': 'ratio',
        'ecode': 'sid',
    }).reset_index()
    df[['sid', 'effective_date', 'ratio']].to_hdf(
        QUANDL_TEMP, "split", complib='blosc', complevel=9)


def preproc_dividend():
    df = pd.read_hdf(QUANDL_TEMP, QUANDL_KEY)

    dividend_rows = []
    for ecode in SYMBOLS:
        equity = df[df.ecode == ecode].copy()
        equity.loc[:, 'ex_date'] = pd.to_datetime(df.date)
        equity.set_index('ex_date', inplace=True)

        dividend_dates = equity[equity.adj_type == 17].index
        if len(dividend_dates) == 0:
            continue
        for dividend_date in dividend_dates:
            loc = equity.index.get_loc(dividend_date)
            if loc == 0:
                raise RuntimeError("Unsupported case")
            prev = equity.iloc[loc - 1]
            dividend_amount = (
                prev['close'] * (
                    1.0 - equity.loc[dividend_date]['adj_factor'])
            )
            dividend_rows.append({
                'ecode': ecode,
                'ex_date': dividend_date,
                'amount': dividend_amount,
            })

    df = pd.DataFrame(dividend_rows)[[
        'ecode', 'ex_date', 'amount',
    ]]
    df.to_hdf(QUANDL_TEMP, 'dividends')


if __name__ == '__main__':
    if not os.path.exists(QUANDL_TEMP):
        preprocessing()
    preproc_split()
    preproc_dividend()
