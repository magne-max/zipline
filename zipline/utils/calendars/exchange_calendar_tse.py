from datetime import time

from pytz import timezone
from japandas.tseries.holiday import TSEHolidayCalendar

from zipline.utils.calendars import TradingCalendar


class TSEExchangeCalendar(TradingCalendar):
    """
    Exchange calendar for the Tokyo Stock Exchange (TSE).

    Open Time: 9:00am, Asia/Tokyo
    Close Time: 3:00pm, Asia/Tokyo
    """
    @property
    def name(self):
        return "TSE"

    @property
    def tz(self):
        return timezone("Asia/Tokyo")

    @property
    def open_time(self):
        return time(9, 00)

    @property
    def close_time(self):
        return time(15, 00)

    @property
    def regular_holidays(self):
        return TSEHolidayCalendar()
