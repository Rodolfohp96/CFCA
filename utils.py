from datetime import date
from datetime import datetime

def gage(_birth):
    today = date.today()
    return today.year - _birth.year - \
            ((today.month, today.day) < (_birth.month, _birth.day))
