# -*- coding: utf-8 -*-
"""
zipline の data bundle として import するための前処理

* unit32 以上の volume は upper bound clip

Author: Kohei
"""
from logging import getLogger, Formatter, StreamHandler, DEBUG
import os
import re
from pathlib import Path

from sklearn.externals.joblib import Parallel, delayed
import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


LOGFORMAT = '%(asctime)s %(levelname)s %(message)s'
TOPIX_FN = "data/input/topix.csv"
NI225_FN = "data/input/ni225.csv"
QUANDL_FN = "data/input/XJPX.zip"
QUANDL_NAME_FN = "data/input/XJPX_L.zip"

COMPRESSION_PARAMS = dict(
    complevel=9,
    complib='blosc',
)

QUANDL_TEMP_FN = "data/working/quandl-xjpx.h5"
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
N_JOBS = 1


def ParallelExecutor(**joblib_args):
    def run(**tq_args):
        def _bar_func(x):
            return tqdm.tqdm(x, **tq_args)

        def _tmp(op_iter):
            return Parallel(**joblib_args)(_bar_func(op_iter))

        return _tmp
    return run


def _filecheck():
    """
    Check required files
    """
    assert Path(TOPIX_FN).exists()
    assert Path(NI225_FN).exists()
    assert Path(QUANDL_FN).exists()
    assert Path(QUANDL_NAME_FN).exists()


def _remove_unadjusted_message(s):
    m = re.search('(^.+)\([\d\.]+\) Unadjusted Stock Prices$', s)
    if m:
        return m.group(1)
    else:
        return s


def preproc_split():
    df = pd.read_hdf(QUANDL_TEMP_FN, 'candlestick')

    # Update index ax
    df.loc[:, 'date'] = pd.to_datetime(df.date)
    df.loc[:, 'date_shift'] = df.date.shift(1)
    df.dropna(subset=['date_shift'], inplace=True)
    df.set_index('date_shift', inplace=True)
    df.index.name = 'effective_date'

    # Select adjustment records
    df = df[(df.adj_type == 6.0) & (df.adj_factor != 1.0)]
    df = df.rename(columns=dict(adj_factor='ratio')).reset_index()
    df = df[['ecode', 'effective_date', 'ratio']]

    with pd.get_store(QUANDL_TEMP_FN, **COMPRESSION_PARAMS) as st:
        st.put('split', df, format='fixed')


def _preproc_dividend_per_ecode(df, calendar_idx, ecode):
    # equity = df[df.ecode == ecode].copy()
    # equity.set_index('date', inplace=True)
    equity = df[df.ecode == ecode].set_index('date')

    dividend_dates = equity[equity.adj_type == 17].index
    if len(dividend_dates) == 0:
        return []

    rows = []
    for dividend_date in dividend_dates:
        loc = equity.index.get_loc(dividend_date)
        if loc == 0:
            logger.warn("Unsupported (unknown adj ratio), {}".format(
                ecode))
            continue

        prev = equity.iloc[loc - 1]
        dividend_amount = (
            prev['close'] * (
                1.0 - equity.loc[dividend_date]['adj_factor'])
        )
        rows.append(dict(
            ecode=ecode, ex_date=dividend_date, amount=dividend_amount))
    return rows


def preproc_dividend():
    df = pd.read_hdf(QUANDL_TEMP_FN, 'candlestick')
    df.loc[:, 'date'] = pd.to_datetime(df.date)
    calendar_idx = pd.Series(index=df.date.unique(), data=df.date.unique())

    # *dirty workaround*
    ecodes = list(df[
        (df.adj_type == 17)
    ].ecode.unique())

    executor = ParallelExecutor(n_jobs=N_JOBS, backend='threading')
    dividend_rows = executor(total=len(ecodes))(delayed(
        _preproc_dividend_per_ecode
    )(df, calendar_idx, ecode) for ecode in ecodes)

    def _flatten(l):
        return [item for sublist in l for item in sublist]

    df = pd.DataFrame(_flatten(dividend_rows))
    df = df[['ecode', 'ex_date', 'amount']]

    with pd.get_store(QUANDL_TEMP_FN, **COMPRESSION_PARAMS) as st:
        st.put('dividends', df, format='fixed')


def preproc_meta():
    df = pd.read_csv(QUANDL_NAME_FN, names=['ecode', 'asset_name'])
    df = df[(df.ecode.str.endswith('_UADJ'))]

    # Remove "XJPX/" prefix and "_UADJ" suffix
    df.loc[:, 'ecode'] = (df.ecode.str[5:-5])
    df.loc[:, 'asset_name'] = df.asset_name.apply(_remove_unadjusted_message)

    with pd.get_store(QUANDL_TEMP_FN, **COMPRESSION_PARAMS) as st:
        st.put('metadata', df, format='fixed')


def preproc_benchmark():
    topix = pd.read_csv(TOPIX_FN)
    topix.loc[:, 'Volume'] = 0.0
    topix.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    topix.loc[:, 'ecode'] = '^TOPIX'
    topix.loc[:, 'date'] = topix.date.apply(
        lambda x: pd.Timestamp(x).strftime("%Y-%m-%d"))
    topix = topix.sort_values(by='date')

    ni225 = pd.read_csv(NI225_FN)
    ni225.drop('Adj Close', axis=1, inplace=True)
    ni225.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    ni225.loc[:, 'ecode'] = '^NI225'
    ni225 = ni225.sort_values(by='date')

    df = pd.concat([topix, ni225])[[
        'ecode', 'date', 'open', 'high',
        'low', 'close', 'volume',
    ]]

    with pd.get_store(QUANDL_TEMP_FN, **COMPRESSION_PARAMS) as st:
        st.put('benchmark', df, format='fixed')


def preproc_candlestick():
    df = pd.read_csv(QUANDL_FN, names=QUANDL_XJPX_COLS)
    df = df[(df.ecode.str.endswith('_UADJ'))]

    clip_sz = len(df[df.volume > MAX_VOL])
    if clip_sz > 0:
        logger.warn(">>> {} values will be cliped.".format(clip_sz))

    # Remove "_UADJ" suffix
    df.loc[:, 'ecode'] = df.ecode.str[:-5]

    # Clip large values to handle on zipline.
    df.loc[:, 'volume'] = df.volume.clip(0, MAX_VOL)

    with pd.get_store(QUANDL_TEMP_FN, **COMPRESSION_PARAMS) as st:
        st.put('candlestick', df, format='fixed')


def main():
    # logger.info("Processing metadata...")
    # preproc_meta()

    # logger.info("Processing candlestick...")
    # preproc_candlestick()

    # logger.info("Processing benchmark...")
    # preproc_benchmark()

    # logger.info("Processing split...")
    # preproc_split()

    logger.info("Processing dividend...")
    preproc_dividend()


if __name__ == '__main__':
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    handler.setFormatter(Formatter(LOGFORMAT))
    logger = getLogger(__name__)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)

    _filecheck()
    main()
