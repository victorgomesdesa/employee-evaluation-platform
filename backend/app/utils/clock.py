from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def get_current_datetime() -> datetime:
    return datetime.now(APP_TIMEZONE)


def get_week_reference(current_datetime: datetime) -> date:
    localized_datetime = current_datetime.astimezone(APP_TIMEZONE)
    return localized_datetime.date() - timedelta(days=localized_datetime.weekday())
