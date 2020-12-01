from timewrapper import Time
from math import ceil

class Event:

    def __init__(self, date, eventType, duration=0, comment=""):
        self.date = Time.parse(date)
        self.type = eventType
        self.duration = duration
        self.comment = comment

    def serialize(self):
        if self.comment:
            return {self.date.format(): [self.type, self.duration, self.comment]}
        else:
            return {self.date.format(): [self.type, self.duration]}

    def __repr__(self):
        return f"{{{self.date.format()}, {self.type}, {self.duration}, {self.comment}}}"

    def __str__(self):
        return f"{self.date.format(options='weekday'):>15s} | {self.type:10s} {Time.reformat(self.duration)} | {self.comment}"

    def edit(self):
        while True:
            print(f"  {self.date.format():>15s} | {self.type:10s} {Time.reformat(self.duration)} | {self.comment}")
            field = input("\nField (Date|Type|Period|Comment)> ").lower()

            if 'date'.startswith(field):
                newDate = input("Date> ")
                d = self.date.format().split(' ')
                if ":" in newDate and "." in newDate:
                    self.date = Time.parse(newDate)
                elif ":" in newDate:
                    try:
                        self.date = Time.parse(f"{d[0]} {newDate}")
                    except:
                        self.date = Time.parse(f"{d[0]} {newDate}", "YYYY-MM-DD H:mm")
                elif "." in newDate:
                    try:
                        self.date = Time.parse(f"{newDate}{d[0].split('-')[0]} {d[1]}", ["DD.MM.YYYY HH:mm", "D.MM.YYYY HH:mm", "DD.M.YYYY HH:mm", "D.M.YYYY HH:mm", "D.M."])
                    except Exception:
                        self.date = Time.parse(f"{newDate} {d[1]}", ["DD.MM.YYYY HH:mm", "D.MM.YYYY HH:mm", "DD.M.YYYY HH:mm", "D.M.YYYY HH:mm", "D.M."])
                elif "-" in newDate:
                    self.date = Time.parse(f"{newDate} {d[1]}")
                else:
                    print("Invalid date format")
                    continue
            
            elif 'type'.startswith(field):
                self.type = input("Type> ")
            
            elif 'period'.startswith(field):
                dur = input("Duration (minutes|H:mm)> ")
                if ":" in dur:
                    dur = dur.split(":")
                    dur = int(dur[0]) * 60 + int(dur[1])
                else:
                    dur = int(dur)
                self.duration = ceil(dur/5)*5

            elif 'comment'.startswith(field):
                self.comment = input("Comment> ")
                
            else:
                continue
            
            break
            # print("Number not in range")
        return self

