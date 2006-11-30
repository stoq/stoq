import datetime

from stoqlib.database.runtime import get_current_station, new_transaction
from stoqlib.domain.till import Till

trans = new_transaction()
till = Till(station=get_current_station(trans), connection=trans)
till.open_till()

# Update the opening date to yesterday
yesterday = (datetime.datetime.today() - datetime.timedelta(1)).date()
till.opening_date = yesterday

trans.commit()
