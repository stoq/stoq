from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject import col

########################################
## Date/time columns
########################################

if datetime_available:
    col.default_datetime_implementation = DATETIME_IMPLEMENTATION
    from datetime import datetime, date, time

    class DateTime1(SQLObject):
        col1 = DateTimeCol()
        col2 = DateCol()
        col3 = TimeCol()

    def test_dateTime():
        setupClass(DateTime1)
        _now = datetime.now()
        _today = date.today()
        dt1 = DateTime1(col1=_now, col2=_today, col3=_now.time())

        assert isinstance(dt1.col1, datetime)
        assert dt1.col1.year == _now.year
        assert dt1.col1.month == _now.month
        assert dt1.col1.day == _now.day
        assert dt1.col1.hour == _now.hour
        assert dt1.col1.minute == _now.minute
        assert dt1.col1.second == int(_now.second)

        assert isinstance(dt1.col2, date)
        assert dt1.col2.year == _today.year
        assert dt1.col2.month == _today.month
        assert dt1.col2.day == _today.day

        assert isinstance(dt1.col3, time)
        assert dt1.col3.hour == _now.hour
        assert dt1.col3.minute == _now.minute
        assert dt1.col3.second == int(_now.second)

if mxdatetime_available:
    col.default_datetime_implementation = MXDATETIME_IMPLEMENTATION
    from mx.DateTime import now, Time

    dateFormat = None # use default
    if getConnection().dbName == "sqlite":
        from sqlobject.sqlite.sqliteconnection import using_sqlite2
        if using_sqlite2: # PySQLite2 returns full date/time for a date
            dateFormat = "%Y-%m-%d %H:%M:%S"

    class DateTime2(SQLObject):
        col1 = DateTimeCol()
        col2 = DateCol(dateFormat=dateFormat)
        col3 = TimeCol()

    def test_mxDateTime():
        setupClass(DateTime2)
        _now = now()
        dt2 = DateTime2(col1=_now, col2=_now, col3=Time(_now.hour, _now.minute, int(_now.second)))

        assert isinstance(dt2.col1, col.DateTimeType)
        assert dt2.col1.year == _now.year
        assert dt2.col1.month == _now.month
        assert dt2.col1.day == _now.day
        assert dt2.col1.hour == _now.hour
        assert dt2.col1.minute == _now.minute
        assert dt2.col1.second == int(_now.second)

        assert isinstance(dt2.col2, col.DateTimeType)
        assert dt2.col2.year == _now.year
        assert dt2.col2.month == _now.month
        assert dt2.col2.day == _now.day
        assert dt2.col1.hour == _now.hour
        assert dt2.col1.minute == _now.minute
        assert dt2.col1.second == int(_now.second)

        assert isinstance(dt2.col3, (col.DateTimeType, col.TimeType))
        assert dt2.col3.hour == _now.hour
        assert dt2.col3.minute == _now.minute
        assert dt2.col3.second == int(_now.second)
