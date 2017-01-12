from zipline.api import symbol, order, record


def initialize(context):
    context.set_benchmark(symbol('TOPIX'))
    context.kobe_steel = symbol('5406')


def handle_data(context, data):
    order(context.kobe_steel, 1)
    record(KobeSteel=data[context.kobe_steel].price)
