# -*- coding: utf-8 -*-
# from __future__ import unicode_literals
import os
import warnings

import numpy as np
import pandas as pd
import pandas.io.data as web
from pandas_datareader.data import DataReader
from boto import connect_s3
import requests
import japandas as jpd
from zipline.utils.cli import maybe_show_progress
from zipline.utils.calendars import register_calendar
from zipline.data.bundles.core import register
from zipline.utils.calendars.exchange_calendar_nyse import NYSEExchangeCalendar


ACCESS_KEY = 'AKIAJHRHBH4FEBEGWPWA'
SECRET_KEY = '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'
BUCKET_NAME = 'zipline-store'
XJPX_PATH = '~/.zipline/data/quandl-xjpx.h5'
ECODES_PATH = '~/.zipline/data/quandl-xjpx.ecodes.csv'


def _cachpath(symbol, type_):
    return '-'.join((symbol.replace(os.path.sep, '_'), type_))


def _download_ecodes():
    conn = connect_s3(ACCESS_KEY, SECRET_KEY)
    bucket = conn.get_bucket(BUCKET_NAME)
    file_key = bucket.get_key(os.path.basename(ECODES_PATH))

    if file_key is None:
        raise RuntimeError("Can't find CSV file on S3 zipline-store bucket.")

    print("downloading quandl-xjpx.ecodes.csv...")
    with open(os.path.expanduser(ECODES_PATH), 'wb') as f:
        file_key.get_contents_to_file(f)

    return os.path.exists(os.path.expanduser(ECODES_PATH))


def _download_hdf():
    conn = connect_s3(ACCESS_KEY, SECRET_KEY)
    bucket = conn.get_bucket(BUCKET_NAME)
    file_key = bucket.get_key(os.path.basename(XJPX_PATH))

    if file_key is None:
        raise RuntimeError("Can't find HDF5 file on S3 zipline-store bucket.")

    print("downloading quandl-xjpx.h5. you may have to wait a few minutes...")
    with open(os.path.expanduser(XJPX_PATH), 'wb') as f:
        file_key.get_contents_to_file(f)

    return os.path.exists(os.path.expanduser(XJPX_PATH))


def quandl_xjpx(symbols, start=None, end=None):
    symbols = tuple(symbols)

    def ingest(environ,
               asset_db_writer,
               minute_bar_writer,  # unused
               daily_bar_writer,
               adjustment_writer,
               calendar,
               start_session,
               end_session,
               cache,
               show_progress,
               output_dir,
               # pass these as defaults to make them 'nonlocal' in py2
               start=start,
               end=end):
        if start is None:
            start = start_session
        if end is None:
            end = end_session

        metadata = pd.DataFrame(np.empty(len(symbols), dtype=[
            ('start_date', 'datetime64[ns]'),
            ('end_date', 'datetime64[ns]'),
            ('auto_close_date', 'datetime64[ns]'),
            ('symbol', 'object'),
        ]))

        if not _download_hdf():
            raise RuntimeError("download step failed.")

        base = pd.read_hdf(os.path.expanduser(XJPX_PATH), 'xjpx')

        def _pricing_iter():
            sid = 0
            with maybe_show_progress(
                    symbols,
                    show_progress,
                    label='Downloading pricing data: ') as it, \
                    requests.Session() as session:
                for symbol in it:
                    path = _cachpath(symbol, 'ohlcv')
                    try:
                        df = cache[path]
                    except KeyError:
                        if symbol == 'TOPIX':
                            df = jpd.DataReader(
                                '998405',
                                'yahoojp',
                                start=start,
                                end=end)
                            df.index.rename('date', inplace=True)
                            df.columns = [
                                'open', 'high', 'low', 'close']
                            df.loc[:, 'volume'] = 0
                            cache[path] = df
                        else:
                            df = base[base.ecode == symbol].copy()
                            df.loc[:, 'date'] = pd.to_datetime(df.date)
                            df.set_index('date', inplace=True)

                            df = df[start:end]
                            df.drop('ecode', axis=1, inplace=True)
                            df = df[[
                                'open',
                                'high',
                                'low',
                                'close',
                                'volume',
                            ]]
                            cache[path] = df

                    # the start date is the date of the first trade and
                    # the end date is the date of the last trade
                    start_date = df.index[0]
                    end_date = df.index[-1]
                    # The auto_close date is the day after the last trade.
                    ac_date = end_date + pd.Timedelta(days=1)
                    metadata.iloc[sid] = (
                        start_date, end_date, ac_date, symbol)

                    yield sid, df
                    sid += 1

        daily_bar_writer.write(_pricing_iter(), show_progress=show_progress)

        symbol_map = pd.Series(metadata.symbol.index, metadata.symbol)

        metadata['exchange'] = "QUANDL-XJPX"
        asset_db_writer.write(equities=metadata)

        adjustments = []
        with maybe_show_progress(
                symbols,
                show_progress,
                label='Downloading adjustment data: ') as it, \
                requests.Session() as session:
            for symbol in it:
                path = _cachpath(symbol, 'adjustment')
                try:
                    df = cache[path]
                except KeyError:
                    df = cache[path] = pd.DataFrame({
                        'action': pd.Series([], dtype='str'),
                        'value': pd.Series([], dtype='str'),
                    })

                df['sid'] = symbol_map[symbol]
                adjustments.append(df)

        adj_df = pd.concat(adjustments)
        adj_df.index.name = 'date'
        adj_df.reset_index(inplace=True)
        splits = adj_df[adj_df.action == 'SPLIT']
        splits = splits.rename(
            columns={'value': 'ratio', 'date': 'effective_date'},
        )
        splits.drop('action', axis=1, inplace=True)

        splits = pd.read_hdf(os.path.expanduser(XJPX_PATH), 'split')
        splits['sid'] = splits.sid.apply(lambda x: symbol_map[x])

        dividends = adj_df[adj_df.action == 'DIVIDEND']
        dividends = dividends.rename(
            columns={'value': 'amount', 'date': 'ex_date'},
        )
        dividends.drop('action', axis=1, inplace=True)

        dividends = pd.read_hdf(os.path.expanduser(XJPX_PATH), 'dividends')
        dividends['sid'] = dividends.ecode.apply(lambda x: symbol_map[x])
        dividends.drop('ecode', axis=1, inplace=True)

        # we do not have this data in the yahoo dataset
        dividends['record_date'] = pd.NaT
        dividends['declared_date'] = pd.NaT
        dividends['pay_date'] = pd.NaT

        adjustment_writer.write(splits=splits, dividends=dividends)

    return ingest


if not os.path.exists(os.path.expanduser(ECODES_PATH)):
    _download_ecodes()

ecodes = pd.read_csv(
    os.path.expanduser(ECODES_PATH)).astype(str).ecode.unique().tolist()


register(
    'quandl-xjpx',
    # quandl_xjpx(['TOPIX'] + ecodes),
    quandl_xjpx(ecodes),
    'QUANDL-XJPX',
    pd.Timestamp('2007-01-04', tz='utc'),
    pd.Timestamp('2016-12-02', tz='utc'),
)
