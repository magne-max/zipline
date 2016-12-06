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
