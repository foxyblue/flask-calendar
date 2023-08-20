from enum import Enum
from datetime import datetime, timedelta
from functools import cached_property
from typing import Callable
from typing import List, Optional, Tuple, cast  # noqa: F401

from flask import abort, current_app, render_template, request
from werkzeug.wrappers import Response

from flask_calendar import constants
from flask_calendar import app_utils
from flask_calendar.calendar_data import CalendarData
from flask_calendar.gregorian_calendar import GregorianCalendar


class CalendarView:
    previous_link: Callable
    next_link: Callable
    defaultday: int
    template: str

    def __init__(self, calendar_id: str) -> None:
        self.calendar_id = calendar_id
        self.calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])
        try:
            self.data = self.calendar_data.load_calendar(calendar_id)
        except FileNotFoundError:
            abort(404)

    @cached_property
    def current_date(self):
        return GregorianCalendar.current_date()

    @property
    def requested_date(self):
        current_day, current_month, current_year = self.current_date
        print("Current", self.current_date)

        year = int(request.args.get("y", current_year))
        year = max(min(year, current_app.config["MAX_YEAR"]), current_app.config["MIN_YEAR"])
        month = int(request.args.get("m", current_month))
        month = max(min(month, 12), 1)
        day = int(request.args.get("d", current_day))
        return day, month, year

    def render(self, view_past_tasks: bool, weekdays_headers: list):
        current_day, current_month, current_year = self.current_date
        day, month, year = self.requested_date
        month_name = GregorianCalendar.MONTH_NAMES[month - 1]

        tasks = self.calendar_data.tasks_from_calendar(
            self.iterdays(self.requested_date),
            self.data,
        )
        tasks = self.calendar_data.add_repetitive_tasks_from_calendar(
            self.iterdays(self.requested_date),
            self.data,
            tasks,
        )

        if not view_past_tasks:
            self.calendar_data.hide_past_tasks(self.iterdays(self.requested_date), self.requested_date, tasks)

        return cast(
            Response,
            render_template(
                self.template,
                calendar_id=self.calendar_id,
                year=year,
                month=month,
                defaultday=self.defaultday,
                month_name=month_name,
                current_year=current_year,
                current_month=current_month,
                current_day=current_day,
                month_days=self.iterdays(self.requested_date),
                previous_link=self.previous_link,
                next_link=self.next_link,
                base_url=current_app.config["BASE_URL"],
                tasks=tasks,
                display_view_past_button=current_app.config["SHOW_VIEW_PAST_BUTTON"],
                weekdays_headers=weekdays_headers,
            ),
        )


class MonthlyView(CalendarView):
    template = "monthly.html"

    @property
    def previous_link(self):
        (_, month, year) = self.requested_date
        return app_utils.previous_month_link(year, month)

    @property
    def next_link(self):
        (_, month, year) = self.requested_date
        return app_utils.next_month_link(year, month)

    @property
    def defaultday(self):
        _, month, day = self.current_date
        _, rmonth, _ = self.requested_date
        if month == rmonth:
            return day
        return 1

    def iterdays(self, current_date):
        def iterr():
            (_, month, year) = current_date
            for date in self.calendar_data.gregorian_calendar.month_days(year, month):
                yield date

        return iterr()


class WeeklyView(CalendarView):
    template = "weekly.html"

    @property
    def previous_link(self):
        _datetime = tuple(reversed(self.requested_date))
        date = datetime(*_datetime) - timedelta(days=7)
        return f"?y={date.year}&m={date.month}&d={date.day}"

    @property
    def next_link(self):
        _datetime = tuple(reversed(self.requested_date))
        date = datetime(*_datetime) + timedelta(days=7)
        return f"?y={date.year}&m={date.month}&d={date.day}"

    @property
    def defaultday(self):
        _, month, _ = self.requested_date
        for day in self.iterdays(self.requested_date):
            if month == day.month:
                return day.day

    def iterdays(self, current_date):
        def iterr():
            (day, month, year) = current_date
            for date in self.calendar_data.gregorian_calendar.week_days(year, month, day):
                yield date

        return iterr()


class DailyView(CalendarView):
    template = "daily.html"

    @property
    def previous_link(self):
        _datetime = tuple(reversed(self.requested_date))
        date = datetime(*_datetime) - timedelta(days=1)
        return f"?y={date.year}&m={date.month}&d={date.day}"

    @property
    def next_link(self):
        _datetime = tuple(reversed(self.requested_date))
        date = datetime(*_datetime) + timedelta(days=1)
        return f"?y={date.year}&m={date.month}&d={date.day}"

    @property
    def defaultday(self):
        day, *_ = self.requested_date
        return day

    def iterdays(self, current_date):
        def iterr():
            yield datetime(*tuple(reversed(self.requested_date)))

        return iterr()


class ViewType(Enum):
    Daily = "daily"
    Weekly = "weekly"
    Monthly = "monthly"


VIEWS = {ViewType.Daily: DailyView, ViewType.Weekly: WeeklyView, ViewType.Monthly: MonthlyView}


def fetch(calendar_id, view_type: ViewType):
    if current_app.config["HIDE_PAST_TASKS"]:
        view_past_tasks = False
    else:
        view_past_tasks = request.cookies.get("ViewPastTasks", "1") == "1"

    if current_app.config["WEEK_STARTING_DAY"] == constants.WEEK_START_DAY_MONDAY:
        weekdays_headers = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    else:
        weekdays_headers = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

    view = VIEWS[view_type](calendar_id)
    return view.render(view_past_tasks, weekdays_headers)
