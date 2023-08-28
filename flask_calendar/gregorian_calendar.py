import calendar
from datetime import date, datetime, timedelta
from typing import Iterable, List, Tuple


class GregorianCalendar:

    MONTH_NAMES = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    @staticmethod
    def setfirstweekday(weekday: int) -> None:
        calendar.setfirstweekday(weekday)

    @staticmethod
    def previous_month_and_year(year: int, month: int) -> Tuple[int, int]:
        previous_month_date = date(year, month, 1) - timedelta(days=2)
        return previous_month_date.month, previous_month_date.year

    @staticmethod
    def next_month_and_year(year: int, month: int) -> Tuple[int, int]:
        last_day_of_month = calendar.monthrange(year, month)[1]
        next_month_date = date(year, month, last_day_of_month) + timedelta(days=2)
        return next_month_date.month, next_month_date.year

    @staticmethod
    def next_12_months(year: int, month: int):
        for _ in range(12):
            month += 1
            if month > 12:
                month = 1
                year += 1
            yield year, month

    @staticmethod
    def current_date() -> Tuple[int, int, int]:
        today_date = datetime.date(datetime.now())
        return today_date.day, today_date.month, today_date.year

    @staticmethod
    def month_days(year: int, month: int) -> Iterable[date]:
        return calendar.Calendar(calendar.firstweekday()).itermonthdates(year, month)

    @staticmethod
    def month_days_with_weekday(year: int, month: int) -> List[List[int]]:
        return calendar.Calendar(calendar.firstweekday()).monthdayscalendar(year, month)

    @staticmethod
    def week_days(year, month, day):
        first_weekday = calendar.firstweekday()

        current_date = datetime(year, month, day)
        current_day = current_date.weekday()

        while current_day != first_weekday:
            current_date -= timedelta(days=1)
            current_day = current_date.weekday()

        for _ in range(7):
            yield current_date
            current_date += timedelta(days=1)

