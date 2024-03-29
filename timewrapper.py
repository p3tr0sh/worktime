import arrow
from math import ceil

def now():
    return arrow.now().replace(second=0,microsecond=0,tzinfo='+00:00')

def today():
    return now().replace(hour=0, minute=0)

def weekstart():
    return today().shift(weekday=6).shift(days=-6)

def monthstart():
    return today().replace(day=1)

class Time:

    timeshift = dict()

    def __init__(self, time, shift=True):
        if shift:
            self.time = time.shift(**Time.timeshift)
        else:
            self.time = time

    def format(self, options=""):
        if options == "weekday":
            return self.time.format(fmt="dddd HH:mm")
        elif options == "dam":
            return self.time.format(fmt="D.MM.")
        return self.time.format(fmt="YYYY-MM-DD HH:mm")

    def __le__(self, item):
        return self.time <= item

    def __ge__(self, item):
        return self.time >= item

    def __lt__(self, item):
        return self.time < item

    def __gt__(self, item):
        return self.time > item

    def shift(self, **kwargs):
        self.time = self.time.shift(**kwargs)
        return self

    def replace(self, **kwargs):
        return Time(self.time.replace(**kwargs), shift=False)

    @staticmethod
    def parse(time, *args, **kwargs):
        return Time(arrow.get(time, *args, **kwargs), shift=False)

    @staticmethod
    def now():
        return Time(now())

    @staticmethod
    def today():
        return Time(today())

    @staticmethod
    def weekstart():
        return Time(weekstart())

    @staticmethod
    def weekend():
        return Time(weekstart().shift(days=7,minutes=-1))

    @staticmethod
    def monthstart():
        return Time(monthstart())
    
    @staticmethod
    def monthend():
        return Time(monthstart().shift(months=1,minutes=-1))

    @staticmethod
    def monthWorkDays():
        result = 0
        runner = Time.monthstart().time
        end = Time.monthend().time
        while runner < end:
            if runner.format("d") not in ["6", "7"]:
                result += 1
            runner = runner.shift(days=1)
        return result

    @staticmethod
    def delta(t1, t2):
        return ceil((t2.time - t1.time).total_seconds() / 60 / 5) * 5

    @staticmethod
    def reformat(minutes):
        if minutes < 0:
            return f"-{abs(minutes // 60 + 1):02d}:{60 - minutes % 60:02d}"
        return f"{minutes//60:02d}:{minutes%60:02d}"
