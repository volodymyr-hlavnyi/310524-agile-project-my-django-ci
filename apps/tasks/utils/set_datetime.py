from django.utils import timezone
import calendar
from datetime import datetime


def last_day_of_month():
    today = timezone.now()
    amount_of_days = calendar.monthrange(today.year, today.month)[1]
    date = datetime(today.year, today.month, amount_of_days)
    return date.astimezone()
