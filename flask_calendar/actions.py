import re
import json
from datetime import date, timedelta
from typing import List, Optional, Tuple, cast  # noqa: F401

import msgspec
from flask import abort, current_app, g, jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug.wrappers import Response

import flask_calendar.constants as constants
from flask_calendar import view
from flask_calendar.weather import Weather, Datapoint
from flask_calendar.app_utils import (
    add_session,
    authenticated,
    authorized,
    get_session_username,
    new_session_id,
)
from flask_calendar.authentication import Authentication
from flask_calendar.calendar_data import CalendarData
from flask_calendar.gregorian_calendar import GregorianCalendar


def get_authentication() -> Authentication:
    auth = getattr(g, "_auth", None)
    if auth is None:
        auth = g._auth = Authentication(
            data_folder=current_app.config["USERS_DATA_FOLDER"],
            password_salt=current_app.config["PASSWORD_SALT"],
            failed_login_delay_base=current_app.config["FAILED_LOGIN_DELAY_BASE"],
        )
    return cast(Authentication, auth)


@authenticated
def index_action() -> Response:
    username = get_session_username(session_id=str(request.cookies.get(constants.SESSION_ID)))
    authentication = get_authentication()
    user_data = authentication.user_data(username)
    return redirect("/{}/".format(user_data["default_calendar"]))


def login_action() -> Response:
    with open("weather.txt") as file:
        payload = json.loads(file.read())

    dataset = [msgspec.convert(item, type=Datapoint) for item in payload]

    weather = Weather(dataset)
    return cast(
        Response,
        render_template(
            "login.html",
            weather=weather,
        ),
    )


def do_login_action() -> Response:
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    authentication = get_authentication()

    if authentication.is_valid(username, password):
        session_id = new_session_id()
        add_session(session_id, username)
        response = make_response(redirect("/"))

        cookie_kwargs = {
            "key": constants.SESSION_ID,
            "value": session_id,
            # 1 month
            "max_age": 2678400,
            "secure": current_app.config["COOKIE_HTTPS_ONLY"],
            "httponly": True,
        }

        samesite_policy = current_app.config.get("COOKIE_SAMESITE_POLICY", None)
        # Certain Flask versions don't support 'samesite' param
        if samesite_policy:
            cookie_kwargs.update({"samesite": samesite_policy})

        response.set_cookie(**cookie_kwargs)
        return cast(Response, response)
    else:
        return redirect("/login")


# @authenticated
# @authorized
def main_calendar_action(calendar_id: str) -> Response:
    view_type = view.ViewType(session.get("view", "monthly"))
    return view.fetch(calendar_id, view_type)


@authenticated
@authorized
def set_view_type(calendar_id: str, view_type: str):
    session["view"] = view_type

    return redirect(url_for("main_calendar_action", calendar_id=calendar_id, **dict(**request.args)))


@authenticated
@authorized
def new_task_action(calendar_id: str, year: int, month: int, day: int) -> Response:
    GregorianCalendar.setfirstweekday(current_app.config["WEEK_STARTING_DAY"])

    current_day, current_month, current_year = GregorianCalendar.current_date()
    year = max(min(int(year), current_app.config["MAX_YEAR"]), current_app.config["MIN_YEAR"])
    month = max(min(int(month), 12), 1)
    month_names = GregorianCalendar.MONTH_NAMES

    day = int(request.args.get("day", day))

    task = {
        "date": CalendarData.date_for_frontend(year, month, day),
        "is_all_day": False,
        "repeats": False,
        "details": "",
    }

    # TODO: Redirect after adding
    return cast(
        Response,
        render_template(
            "task.html",
            calendar_id=calendar_id,
            year=year,
            month=month,
            min_year=current_app.config["MIN_YEAR"],
            max_year=current_app.config["MAX_YEAR"],
            month_names=month_names,
            task=task,
            base_url=current_app.config["BASE_URL"],
            editing=False,
            button_default_color_value=current_app.config["BUTTON_CUSTOM_COLOR_VALUE"],
            buttons_colors=current_app.config["BUTTONS_COLORS_LIST"],
            EMOJI_SECTIONS=current_app.config["EMOJI_SECTIONS"],
        ),
    )


@authenticated
@authorized
def edit_task_action(calendar_id: str, year: int, month: int, day: int, task_id: int) -> Response:
    month_names = GregorianCalendar.MONTH_NAMES
    calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])

    repeats = request.args.get("repeats") == "1"
    try:
        if repeats:
            task = calendar_data.repetitive_task_from_calendar(
                calendar_id=calendar_id, year=year, month=month, task_id=int(task_id)
            )
        else:
            task = calendar_data.task_from_calendar(
                calendar_id=calendar_id,
                year=year,
                month=month,
                day=day,
                task_id=int(task_id),
            )
    except (FileNotFoundError, IndexError):
        abort(404)

    if task["details"] == "&nbsp;":
        task["details"] = ""

    return cast(
        Response,
        render_template(
            "task.html",
            calendar_id=calendar_id,
            year=year,
            month=month,
            day=day,
            min_year=current_app.config["MIN_YEAR"],
            max_year=current_app.config["MAX_YEAR"],
            month_names=month_names,
            task=task,
            base_url=current_app.config["BASE_URL"],
            editing=True,
            button_default_color_value=current_app.config["BUTTON_CUSTOM_COLOR_VALUE"],
            buttons_colors=current_app.config["BUTTONS_COLORS_LIST"],
            EMOJI_SECTIONS=current_app.config["EMOJI_SECTIONS"],
        ),
    )


@authenticated
@authorized
def update_task_action(calendar_id: str, year: str, month: str, day: str, task_id: str) -> Response:
    # Logic is same as save + delete, could refactor but can wait until need to change any save/delete logic

    calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])

    # For creation of "updated" task use only form data
    title = request.form["title"].strip()
    start_date = request.form.get("date", "")
    if len(start_date) > 0:
        fragments = re.split("-", start_date)
        updated_year = int(fragments[0])  # type: Optional[int]
        updated_month = int(fragments[1])  # type: Optional[int]
        updated_day = int(fragments[2])  # type: Optional[int]
    else:
        updated_year = updated_month = updated_day = None
    is_all_day = request.form.get("is_all_day", "0") == "1"
    start_time = request.form["start_time"]
    end_time = request.form.get("end_time", None)
    details = request.form["details"].replace("\r", "").replace("\n", "<br>")
    color = request.form["color"]
    has_repetition = request.form.get("repeats", "0") == "1"
    repetition_type = request.form.get("repetition_type", "")
    repetition_subtype = request.form.get("repetition_subtype", "")
    repetition_value = int(request.form["repetition_value"])  # type: int
    travel_to = request.form.get("travel_to")

    calendar_data.create_task(
        calendar_id=calendar_id,
        year=updated_year,
        month=updated_month,
        day=updated_day,
        title=title,
        is_all_day=is_all_day,
        start_time=start_time,
        end_time=end_time,
        details=details,
        color=color,
        has_repetition=has_repetition,
        repetition_type=repetition_type,
        repetition_subtype=repetition_subtype,
        repetition_value=repetition_value,
        travel_to=travel_to,
    )
    # For deletion of old task data use only url data
    calendar_data.delete_task(
        calendar_id=calendar_id,
        year_str=year,
        month_str=month,
        day_str=day,
        task_id=int(task_id),
    )

    if updated_year is None:
        return redirect("{}/{}/".format(current_app.config["BASE_URL"], calendar_id), code=302)
    else:
        return redirect(
            "{}/{}/?y={}&m={}".format(current_app.config["BASE_URL"], calendar_id, updated_year, updated_month),
            code=302,
        )


@authenticated
@authorized
def save_task_action(calendar_id: str) -> Response:
    title = request.form["title"].strip()
    startdate = request.form.get("date", "")
    enddate = request.form.get("enddate", "")

    if len(startdate) > 0:
        date_fragments = re.split("-", startdate)
        year = int(date_fragments[0])  # type: Optional[int]
        month = int(date_fragments[1])  # type: Optional[int]
        day = int(date_fragments[2])  # type: Optional[int]
    else:
        year = month = day = None
    is_all_day = request.form.get("is_all_day", "0") == "1"
    start_time = request.form["start_time"]
    end_time = request.form.get("end_time", None)
    details = request.form["details"].replace("\r", "").replace("\n", "<br>")
    color = request.form["color"]
    has_repetition = request.form.get("repeats", "0") == "1"
    repetition_type = request.form.get("repetition_type")
    repetition_subtype = request.form.get("repetition_subtype")
    repetition_value = int(request.form["repetition_value"])

    calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])

    dates_to_create = []  # type: List[Tuple[Optional[int], Optional[int], Optional[int]]]

    # repetitive tasks not supported
    if startdate != enddate and not has_repetition:
        startdate_fragments = re.split("-", startdate)
        enddate_fragments = re.split("-", enddate)
        sdate = date(int(startdate_fragments[0]), int(startdate_fragments[1]), int(startdate_fragments[2]))
        edate = date(int(enddate_fragments[0]), int(enddate_fragments[1]), int(enddate_fragments[2]))
        delta = edate - sdate
        for i in range(delta.days + 1):
            currentdate = re.split("-", str(sdate + timedelta(days=i)))

            year = int(currentdate[0])
            month = int(currentdate[1])
            day = int(currentdate[2])

            dates_to_create.append((year, month, day))
    else:
        dates_to_create.append((year, month, day))

    for date_tuple in dates_to_create:
        year, month, day = date_tuple
        calendar_data.create_task(
            calendar_id=calendar_id,
            year=year,
            month=month,
            day=day,
            title=title,
            is_all_day=is_all_day,
            start_time=start_time,
            end_time=end_time,
            details=details,
            color=color,
            has_repetition=has_repetition,
            repetition_type=repetition_type,
            repetition_subtype=repetition_subtype,
            repetition_value=repetition_value,
        )

    if year is None:
        return redirect("{}/{}/".format(current_app.config["BASE_URL"], calendar_id), code=302)
    else:
        return redirect(
            "{}/{}/?y={}&m={}".format(current_app.config["BASE_URL"], calendar_id, year, month),
            code=302,
        )


@authenticated
@authorized
def delete_task_action(calendar_id: str, year: str, month: str, day: str, task_id: str) -> Response:
    calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])
    calendar_data.delete_task(
        calendar_id=calendar_id,
        year_str=year,
        month_str=month,
        day_str=day,
        task_id=int(task_id),
    )

    return cast(Response, jsonify({}))


@authenticated
@authorized
def update_task_day_action(calendar_id: str, year: str, month: str, day: str, task_id: str) -> Response:
    new_day = request.data.decode("utf-8")

    calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])
    calendar_data.update_task_day(
        calendar_id=calendar_id,
        year_str=year,
        month_str=month,
        day_str=day,
        task_id=int(task_id),
        new_day_str=new_day,
    )

    return cast(Response, jsonify({}))


@authenticated
@authorized
def hide_repetition_task_instance_action(calendar_id: str, year: str, month: str, day: str, task_id: str) -> Response:
    calendar_data = CalendarData(current_app.config["DATA_FOLDER"], current_app.config["WEEK_STARTING_DAY"])
    calendar_data.hide_repetition_task_instance(
        calendar_id=calendar_id,
        year_str=year,
        month_str=month,
        day_str=day,
        task_id_str=task_id,
    )

    return cast(Response, jsonify({}))
