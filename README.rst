.. image:: https://media.quantopian.com/logos/open_source/zipline-logo-03_.png
    :target: http://www.zipline.io
    :width: 212px
    :align: center
    :alt: Zipline

Zipline-ja
==========

Zipline で国内銘柄を扱ったバックテストができるようにフォークしたパッケージです。

利用できる４本足データの確認：

.. code:: bash

    $ PYTHONWARNINGS="ignore" zipline bundles
    quandl <no ingestions>
    quandl-xjpx <no ingestions>
    quantopian-quandl <no ingestions>

このうち `quandl`, `quantopian-quandl` は Quantopian が定義した US 向けのデータ。
`quandl-xjpx` が国内銘柄向けに新たに定義したデータ。

.. code:: bash

    $ PYTHONWARNINGS="ignore" zipline ingest -b quandl-xjpx
    downloading quandl-xjpx.ecodes.csv...
    downloading quandl-xjpx.h5. you may have to wait a few minutes...
    (snip)

やや時間がかかる（要修正）
データの取得が終わったら、このデータを使って以下のサンプルアルゴリズムを動かすことができる。

.. code:: python

    from zipline.api import sid, symbol, order, record, get_datetime
    import logbook
    import pandas as pd
    
    
    log = logbook.Logger("ZiplineLog")
    
    
    def initialize(context):
        context.set_benchmark(symbol('TOPIX'))
        context.assets = [
            symbol(sym_str)
            for sym_str in [
                '2121',
                '4689',
                '7162',
            ]
        ]
    
    
    def handle_data(context, data):
        # log.info(data.history(context.assets, "price", 20, "1d"))
        # log.info(data.current(context.assets, "volume"))
        # exchange_ts = pd.Timestamp(get_datetime()).tz_convert('Asia/Tokyo')
        # exchange_ts = pd.Timestamp(get_datetime())
        log.info(pd.Timestamp(get_datetime()).tz_convert('Asia/Tokyo'))
        log.info(str(data[symbol('TOPIX')].price))
    
        order(symbol('4689'), -10)
        record(Yahoo=data[symbol('4689')].price)
    
    
    def analyze(context, perf):
        pass  # print(perf.iloc[-1].T)


この例は market close のタイミングで 4689 をショートし続け、
TOPIX の値段（close price）をログに記録し続けるロジックである。

.. code:: bash

    $ PYTHONWARNINGS="ignore" zipline run \
        -f zipline/examples/buy_test.py \
        --bundle quandl-xjpx \
        --start 2016-09-01 \
        --end 2016-09-22 \
        --data-frequency daily \
        -o result.pickle
    [2016-12-06 04:22:34.903645] INFO: Loader: Cache at /Users/kohozaki/.zipline/data/^GSPC_benchmark.csv does not have data from 1990-01-02 00:00:00+00:00 to 2016-12-02 00:00:00+00:00.
    Downloading benchmark data for '^GSPC'.
    [2016-12-06 04:22:41.692484] INFO: ZiplineLog: 2016-09-01 15:00:00+09:00
    [2016-12-06 04:22:41.693996] INFO: ZiplineLog: 1337.38
    [2016-12-06 04:22:41.711374] INFO: ZiplineLog: 2016-09-02 15:00:00+09:00
    [2016-12-06 04:22:41.712054] INFO: ZiplineLog: 1340.76
    [2016-12-06 04:22:41.790409] INFO: ZiplineLog: 2016-09-05 15:00:00+09:00
    [2016-12-06 04:22:41.791120] INFO: ZiplineLog: 1343.8500000000001
    [2016-12-06 04:22:41.810931] INFO: ZiplineLog: 2016-09-06 15:00:00+09:00
    [2016-12-06 04:22:41.811371] INFO: ZiplineLog: 1352.58
    [2016-12-06 04:22:41.819929] INFO: ZiplineLog: 2016-09-07 15:00:00+09:00
    [2016-12-06 04:22:41.820631] INFO: ZiplineLog: 1349.53
    [2016-12-06 04:22:41.829482] INFO: ZiplineLog: 2016-09-08 15:00:00+09:00
    [2016-12-06 04:22:41.830000] INFO: ZiplineLog: 1345.95
    [2016-12-06 04:22:41.839807] INFO: ZiplineLog: 2016-09-09 15:00:00+09:00
    [2016-12-06 04:22:41.840325] INFO: ZiplineLog: 1343.8600000000001
    [2016-12-06 04:22:41.857832] INFO: ZiplineLog: 2016-09-12 15:00:00+09:00
    [2016-12-06 04:22:41.858479] INFO: ZiplineLog: 1323.1000000000001
    [2016-12-06 04:22:41.869708] INFO: ZiplineLog: 2016-09-13 15:00:00+09:00
    [2016-12-06 04:22:41.870110] INFO: ZiplineLog: 1322.99
    [2016-12-06 04:22:41.878526] INFO: ZiplineLog: 2016-09-14 15:00:00+09:00
    [2016-12-06 04:22:41.879111] INFO: ZiplineLog: 1314.74
    [2016-12-06 04:22:41.889228] INFO: ZiplineLog: 2016-09-15 15:00:00+09:00
    [2016-12-06 04:22:41.890548] INFO: ZiplineLog: 1301.1100000000001
    [2016-12-06 04:22:41.901059] INFO: ZiplineLog: 2016-09-16 15:00:00+09:00
    [2016-12-06 04:22:41.901663] INFO: ZiplineLog: 1311.5
    [2016-12-06 04:22:41.910515] INFO: ZiplineLog: 2016-09-20 15:00:00+09:00
    [2016-12-06 04:22:41.910957] INFO: ZiplineLog: 1316.97
    [2016-12-06 04:22:41.918634] INFO: ZiplineLog: 2016-09-21 15:00:00+09:00
    [2016-12-06 04:22:41.919093] INFO: ZiplineLog: 1352.67
    [2016-12-06 04:22:41.925971] INFO: Performance: Simulated 14 trading days out of 14.
    [2016-12-06 04:22:41.926089] INFO: Performance: first open: 2016-09-01 00:00:00+00:00
    [2016-12-06 04:22:41.926165] INFO: Performance: last close: 2016-09-21 06:00:00+00:00

パフォーマンスは `result.pickle` に出力される。これは `pandas.read_pickle` でロードできる。

Zipline
=======

|Gitter|
|version status|
|travis status|
|appveyor status|
|Coverage Status|

Zipline is a Pythonic algorithmic trading library. It is an event-driven
system that supports both backtesting and live-trading.

Zipline is currently used in production as the backtesting and live-trading
engine powering `Quantopian <https://www.quantopian.com>`_ -- a free,
community-centered, hosted platform for building and executing trading
strategies.

`Join our
community! <https://groups.google.com/forum/#!forum/zipline>`_

`Documentation <http://www.zipline.io>`_

Want to contribute? See our `open
requests <https://github.com/quantopian/zipline/wiki/Contribution-Requests>`_
and our `general
guidelines <https://github.com/quantopian/zipline#contributions>`_
below.

Features
========

- Ease of use: Zipline tries to get out of your way so that you can
  focus on algorithm development. See below for a code example.
- Zipline comes "batteries included" as many common statistics like
  moving average and linear regression can be readily accessed from
  within a user-written algorithm.
- Input of historical data and output of performance statistics are
  based on Pandas DataFrames to integrate nicely into the existing
  PyData eco-system.
- Statistic and machine learning libraries like matplotlib, scipy,
  statsmodels, and sklearn support development, analysis, and
  visualization of state-of-the-art trading systems.

Installation
============

Installing With ``pip``
-----------------------

Assuming you have all required (see note below) non-Python dependencies, you
can install Zipline with ``pip`` via:

.. code-block:: bash

    $ pip install zipline

**Note:** Installing Zipline via ``pip`` is slightly more involved than the
average Python package.  Simply running ``pip install zipline`` will likely
fail if you've never installed any scientific Python packages before.

There are two reasons for the additional complexity:

1. Zipline ships several C extensions that require access to the CPython C API.
   In order to build the C extensions, ``pip`` needs access to the CPython
   header files for your Python installation.

2. Zipline depends on `numpy <http://www.numpy.org/>`_, the core library for
   numerical array computing in Python.  Numpy depends on having the `LAPACK
   <http://www.netlib.org/lapack>`_ linear algebra routines available.

Because LAPACK and the CPython headers are binary dependencies, the correct way
to install them varies from platform to platform.  On Linux, users generally
acquire these dependencies via a package manager like ``apt``, ``yum``, or
``pacman``.  On OSX, `Homebrew <http://www.brew.sh>`_ is a popular choice
providing similar functionality.

See the full `Zipline Install Documentation`_ for more information on acquiring
binary dependencies for your specific platform.

conda
-----

Another way to install Zipline is via the ``conda`` package manager, which
comes as part of `Anaconda <http://continuum.io/downloads>`_ or can be
installed via ``pip install conda``.

Once set up, you can install Zipline from our ``Quantopian`` channel:

.. code-block:: bash

    conda install -c Quantopian zipline

Currently supported platforms include:

-  GNU/Linux 64-bit
-  OSX 64-bit
-  Windows 64-bit

.. note::

   Windows 32-bit may work; however, it is not currently included in
   continuous integration tests.

Quickstart
==========

See our `getting started
tutorial <http://www.zipline.io/#quickstart>`_.

The following code implements a simple dual moving average algorithm.

.. code:: python

    from zipline.api import (
        history,
        order_target,
        record,
        symbol,
    )


    def initialize(context):
        context.i = 0


    def handle_data(context, data):
        # Skip first 300 days to get full windows
        context.i += 1
        if context.i < 300:
            return

        # Compute averages
        # history() has to be called with the same params
        # from above and returns a pandas dataframe.
        short_mavg = history(100, '1d', 'price').mean()
        long_mavg = history(300, '1d', 'price').mean()

        sym = symbol('AAPL')

        # Trading logic
        if short_mavg[sym] > long_mavg[sym]:
            # order_target orders as many shares as needed to
            # achieve the desired number of shares.
            order_target(sym, 100)
        elif short_mavg[sym] < long_mavg[sym]:
            order_target(sym, 0)

        # Save values for later inspection
        record(AAPL=data[sym].price,
               short_mavg=short_mavg[sym],
               long_mavg=long_mavg[sym])

You can then run this algorithm using the Zipline CLI. From the command
line, run:

.. code:: bash

    zipline run -f dual_moving_average.py --start 2011-1-1 --end 2012-1-1 -o dma.pickle

This will download the AAPL price data from Yahoo! Finance in the
specified time range and stream it through the algorithm and save the
resulting performance dataframe to dma.pickle which you can then load
and analyze from within python.

You can find other examples in the zipline/examples directory.

Contributions
=============

If you would like to contribute, please see our Contribution Requests:
https://github.com/quantopian/zipline/wiki/Contribution-Requests

.. |Gitter| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/quantopian/zipline?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. |version status| image:: https://img.shields.io/pypi/pyversions/zipline.svg
   :target: https://pypi.python.org/pypi/zipline
.. |travis status| image:: https://travis-ci.org/quantopian/zipline.png?branch=master
   :target: https://travis-ci.org/quantopian/zipline
.. |appveyor status| image:: https://ci.appveyor.com/api/projects/status/3dg18e6227dvstw6/branch/master?svg=true
   :target: https://ci.appveyor.com/project/quantopian/zipline/branch/master
.. |Coverage Status| image:: https://coveralls.io/repos/quantopian/zipline/badge.png
   :target: https://coveralls.io/r/quantopian/zipline

.. _`Zipline Install Documentation` : http://www.zipline.io/install.html
