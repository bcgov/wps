from zoneinfo import ZoneInfo
from datetime import date, datetime, time


def pin_issue_date_to_time(issue_date: date, issue_time: time):
    """ Pin the time of an issue date to given time"""
    return datetime.combine(issue_date, issue_time, tzinfo=ZoneInfo('America/Vancouver'))


def morning_time(issue_date: date):
    """ Pin the time of an issue date to morning time, 08:00 """
    return pin_issue_date_to_time(issue_date, time(8, 0, 0))


def noon_time(issue_date: date):
    """ Pin the time of an issue date to noon time, 13:00 """
    return pin_issue_date_to_time(issue_date, time(13, 0, 0))


def evening_time(issue_date: date):
    """ Pin the time of an issue date to evening time, 16:45 """
    return pin_issue_date_to_time(issue_date, time(16, 45, 0))
