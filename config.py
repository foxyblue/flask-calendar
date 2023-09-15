import flask_calendar.constants as constants

DEBUG = True
DATA_FOLDER = "data"
USERS_DATA_FOLDER = "users"
BASE_URL = "http://0.0.0.0:5000"
MIN_YEAR = 2017
MAX_YEAR = 2200
PASSWORD_SALT = "something random and full of non-standard characters"
SECRET_KEY = "hahah"
HOST_IP = "0.0.0.0"  # set to None for production
LOCALE = "en_US.UTF-8"
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE = "US/Central"

WEEK_STARTING_DAY = constants.WEEK_START_DAY_MONDAY

MONTHS_TO_EXPORT = 6  # currently only used for ICS export

FEATURE_FLAG_ICAL_EXPORT = False

# (base ^ attempts ) second delays between failed logins
FAILED_LOGIN_DELAY_BASE = 2

# If true, will automatically decorate hyperlinks with <a> tags upon rendering them
AUTO_DECORATE_TASK_DETAILS_HYPERLINK = True

SHOW_VIEW_PAST_BUTTON = True

# Of use if SHOW_VIEW_PAST_BUTTON is False
HIDE_PAST_TASKS = False

# days past to keep hidden tasks (future ones always kept) counting all months as 31 days long
DAYS_PAST_TO_KEEP_HIDDEN_TASKS = 62

# Cookies config
COOKIE_HTTPS_ONLY = False
COOKIE_SAMESITE_POLICY = "Lax"

# If to render emoji buttons at the task create/edit page
EMOJIS_ENABLED = True

# Colors for new task buttons
BUTTON_CUSTOM_COLOR_VALUE = "#7bd188"
BUTTONS_COLORS_LIST = (
    ("#ffa6a6", "Red"),
    ("#7bd188", "Green"),
    ("#a0c0ea", "Blue"),
    ("#bebebe", "Grey"),
    ("#dfb5a2", "Brown"),
    ("#beb6f3", "Purple"),
    ("#f5b356", "Orange"),
    ("#dbdbdb", "Black"),
)
# Emojis for new task buttons
EMOJI_SECTIONS = {
    "travel": ["🌍", "🏨", "🗺️", "📷", "🏙️", "⛺"],
    "transport": ["🚗", "🚕", "🚲", "🚂'", "🚆", "🚌", "🚢", "🛂", "✈️", "🚁", "🧳"],
    "eating": ["🍔", "🍕", "🍝", "🍣", "🍦", "☕", "🍰", "🍿", "🥗"],
    "activities": ["🎿", "⛷️", "🏂"],
    "accommodation": ["🛌", "😴", "🏡"],
    "sites": ["⛩️", "🏯", "🌸", "🌄", "🗼"],
    "flags": ["🇯🇵", "🇰🇷", "🇳🇴", "🇸🇪"],
}


# percent of chance to do a GC-like sweep on save and clean empty and/or past hidden entries.
# values [0, 100] -> Note that 0 disables it, 100 makes it run every time
GC_ON_SAVE_CHANCE = 30
