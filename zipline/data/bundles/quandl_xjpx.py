"""

"""
from io import BytesIO
from itertools import count
import tarfile
from time import time, sleep

from click import progressbar
from logbook import Logger
import pandas as pd
import requests
from six.moves.urllib.parse import urlencode
from boto import connect_s3
import tarfile

from . import core as bundles
from zipline.utils.cli import maybe_show_progress

log = Logger(__name__)
seconds_per_call = (pd.Timedelta('10 minutes') / 2000).total_seconds()
# Invalid symbols that quandl has had in its metadata:
excluded_symbols = frozenset({'TEST123456789'})


ACCESS_KEY = 'AKIAJHRHBH4FEBEGWPWA'
SECRET_KEY = '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'
BUCKET_NAME = 'zipline-store'


@bundles.register('quandl-xjpx', create_writers=False)
def quandl_xjpx_bundle(environ,
                       asset_db_writer,
                       minute_bar_writer,
                       daily_bar_writer,
                       adjustment_writer,
                       calendar,
                       start_session,
                       end_session,
                       cache,
                       show_progress,
                       output_dir):
    conn = connect_s3(ACCESS_KEY, SECRET_KEY)
    bucket = conn.get_bucket(BUCKET_NAME)
    file_key = bucket.get_key('quandl-xjpx.tar')
    bs = BytesIO()
    file_key.get_contents_to_file(bs)
    bs.seek(0)

    with tarfile.open('r', fileobj=bs) as tar:
        tar.extractall(output_dir)
