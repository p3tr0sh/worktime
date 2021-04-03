#!/usr/bin/env python3



import argparse
import os.path
import json
from math import ceil

from os import get_terminal_size

import subprocess

from timewrapper import Time
from event import Event

def toMinutes(number, unit):
    if unit == "h":
        return int(number) * 60
    if unit == "m":
        return int(number)

class Calendar:

    def __init__(self, confFile):
        self.events = dict()
        self.target = dict()
        self.weekTarget = 0
        self.dayTarget = 0
        self.categories = [] # dict with color codes, random color to begin with, choose color
        self.focus = ""
        self.current = False

        self.conffile = confFile

        self.read()

    def workPerMonth(self):
        monthcounter = 0
        monthid = '0'
        counterdict = dict()
        for evt in self.events.values():
            idd = evt.date.time.format('YYYY-MM')
            if idd not in counterdict:
                counterdict[idd] = 0
            if evt.type == self.focus and not evt.comment == "Wochenübertrag":
                # print(evt)
                counterdict[idd] += evt.duration
        for k, v in counterdict.items():
            print(k, Time.reformat(v))

    def calculateTartetTime(self):
        if self.target['type'] == "weekly":
            
            self.weekTarget = toMinutes(self.target['amount'], self.target['unit'])
            self.dayTarget = self.weekTarget / 5
        elif self.target['type'] == "monthly":
            workdaysInMonth = Time.monthWorkDays()
            # simple hack
            self.weekTarget = toMinutes(self.target['amount'], self.target['unit']) / workdaysInMonth * 5
            print(Time.reformat(int(self.weekTarget)))
        exit(0)

    def read(self):
        with open(os.path.expanduser(self.conffile), 'r') as conffile:
            config = json.load(conffile)
            self.filename = config['name']
            self.target = config['target']
            self.categories = config['categories']
            self.focus = config['focus']

        with open(os.path.expanduser(self.filename), 'r') as calfile:
            cal = json.load(calfile)
            self.current = cal['current']
            if self.current:
                self.current = Event(self.current[0], self.current[1][0], duration=Time.delta(Time.parse(self.current[0]), Time.now()), comment='-- CURRENT SESSION --')
            for date, event in cal['events'].items():
                self.events[date] = Event(date, *event)
    
    def write(self):
        with open(os.path.expanduser(self.conffile), 'w') as conffile:
            obj = dict()
            obj['name'] = self.filename
            obj['target'] = self.target
            obj['categories'] = self.categories
            obj['focus'] = self.focus
            json.dump(obj, conffile, indent=2, ensure_ascii=False)

        with open(os.path.expanduser(self.filename), 'w') as calfile:
            obj = dict()
            if self.current:
                obj['current'] = list(self.current.serialize().items())[0]
            else: 
                obj['current'] = False
            obj['events'] = dict()
            for event in self.events.values():
                obj['events'].update(event.serialize())
            json.dump(obj, calfile, indent=2, ensure_ascii=False)
        

    def getWeek(self, withCurrent=False):
        weekstart = Time.weekstart()
        weekend   = Time.weekend()
        week = []
        for event in self.events.values():
            if event.date >= weekstart and event.date <= weekend:
                week.append(event)
        if withCurrent and self.current:
            if self.current.date >= weekstart and self.current.date <= weekend:
                week.append(self.current)
        return sorted(week, key=lambda x: x.date.format())
    
    def getMonth(self, withCurrent=False):
        monthstart = Time.monthstart()
        monthend   = Time.monthend()
        month = []
        for event in self.events.values():
            if event.date > monthstart and event.date < monthend and not event.comment == "Wochenübertrag":
                month.append(event)
        if withCurrent and self.current:
            if self.current.date >= monthstart and self.current.date <= monthend:
                month.append(self.current)
        return sorted(month, key=lambda x: x.date.format())

    def getOvertime(self, focus=""):
        if focus == "":
            focus = self.focus
        lastweekend = Time.weekstart().shift(minutes=-1)
        try:
            if self.events[lastweekend.format()].type == focus and self.events[lastweekend.format()].comment == "Wochenübertrag":
                return self.events[lastweekend.format()].duration
            return 0
        except KeyError:
            return 0

    def getDay(self):
        day = Time.today().format().split(" ")[0]
        evts = []
        for date in self.events.keys():
            if date.startswith(day):
                evts.append(self.events[date])
        return evts

    def toggle(self, option):
        if not self.current:
            x = Time.now()
            self.current = Event(x.format(), option)
            if option not in self.categories:
                self.categories.append(option)
        else:
            self.current.duration = Time.delta(self.current.date, Time.now())
            self.current.comment = option
            self.events[self.current.date.format()] = self.current
            self.current = False
        self.write()

    def bar(self, focus=""):
        if self.current:
            focus = self.current.type
        else: 
            focus = self.focus
        weekminutes = 0

        weekminutes -= self.getOvertime(focus)

        for event in self.getWeek():
            if event.type == focus:
                weekminutes += event.duration

        dayminutes = 0

        for event in self.getDay():
            if event.type == focus:
                if event.comment != "Wochenübertrag":
                    dayminutes += event.duration
        
        now = 0
        if self.current and self.current.type == focus:
            now += Time.delta(self.current.date, Time.now())

        weekminutes += now
        dayminutes += now
        targetReached = weekminutes >= self.target and focus == self.focus
        print(f"{Time.reformat(weekminutes)}|{Time.reformat(dayminutes)}")
        print(f"{Time.reformat(dayminutes)}")
        if self.current and self.current.type == focus:
            print("#33AAFF")
        elif targetReached:
            print("#00AA00")
        else:
            print("#AAAAAA")

    def calendarview(self):
        # setup the calendar design
        width, height = get_terminal_size()
        height = 48
        daywidth = width // 7 if width%7 >= 3 else (width // 7) - 1
        timewidth = width - 7 * daywidth
        timecolumn = [f"{i//2:02d}:00" + " "*(timewidth-5) if (i/2)%3==0 else " "*timewidth for i in range(height)]
        matrix = [[f' |\033[1;36m{"·"*(daywidth-4)}\033[0m| ' for x in range(7)] if (y/2)%3==0 else [f' |{"·"*(daywidth-4)}| ' for x in range(7)] for y in range(height)]
        earliest = 47
        latest = 0

        def putEvent(matrix, event, earliest, latest):
            time = event.date.format().split(" ")[1]
            ystart = int(time.split(":")[0]) * 2 + (int(time.split(":")[1]) > 30)
            eventheight = ceil(event.duration/30)
            earliest = min(ystart, earliest)
            latest = max(latest, ystart+eventheight)
            inner = daywidth - 6
            dayoff = 0
            weekday = event.date.time.weekday()
            for i in range(eventheight):
                if ystart + i == height:
                    dayoff = 1
                    if dayoff + weekday > 6:
                        break
                earliest = min(earliest, ystart+i - (dayoff * height))
                matrix[ystart+i - (dayoff * height)][weekday + dayoff] = f'\033[33m |{" "*(daywidth-4)}| \033[0m'
                if i >= 1 and i + 1 == eventheight:
                    matrix[ystart+i - (dayoff * height)][weekday + dayoff] = f'\033[33m +{"-"*(daywidth-4)}+ \033[0m'
                if i >= 1 and event.comment != "" and (i-1) * inner < len(event.comment):
                    matrix[ystart+i - (dayoff * height)][weekday + dayoff] = \
                        f'\033[33m | {event.comment[(i-1)*inner:min(len(event.comment),i*inner)]:{inner}s} | \033[0m'
            headline = event.type
            headline = f" {headline[:min(len(headline),daywidth-6)]} "
            matrix[ystart][weekday] = f"\033[33m +{headline:-^{daywidth-4}s}+ \033[0m"
            return (matrix, earliest, latest)

        for event in self.getWeek(withCurrent=True):
            if event.comment == "Wochenübertrag":
                continue
            matrix, earliest, latest = putEvent(matrix, event, earliest, latest)
                

        earliest = int(earliest/6)*6
        latest = ceil(latest/6)*6

        dates = [Time.weekstart().shift(days=x).format(options="dam") for x in range(7)]
        if latest > 0:
            print(" "*timewidth, end="\033[1;36m")
            for w, d in zip(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], dates):
                if daywidth >= 18:
                    header = f" {w} {d}"
                else:
                    header = w
                print(f"{header:^{daywidth}s}", end="")
            print("\033[0m")
        for row, data in enumerate(zip(matrix,timecolumn)):
            if row < earliest or row > latest:
                continue
            print(f'\033[1;36m{data[1]}\033[0m', end="")
            data[0][-1] = data[0][-1][:-1]
            for it in data[0]:
                print(it, end="")
            print()

    def listview(self):
        events = self.getWeek(withCurrent=True)
        try:
            previousDay = events[0].date.format().split(' ')[0]
        except:
            print("Nothing to show yet...")
            return

        for event in events:
            if not event.date.format().startswith(previousDay):
                previousDay = event.date.format().split(' ')[0]
                print()
            print(event)

    def summaryview(self):
        week = self.getWeek(withCurrent=True)
        month = self.getMonth(withCurrent=True)
        weeksums = {k: sum([x.duration for x in week if x.type == k]) for k in self.categories}
        monthsums = {k: sum([x.duration for x in month if x.type == k]) for k in self.categories}
        if self.focus in weeksums:
            weeksums[self.focus] -= self.getOvertime()
        print("WEEK ------------")
        for k, v in weeksums.items():
            v = f"{v//60:02d}:{v%60:02d}"
            print(f"  {k:7s} {v}")
        print()
        print("MONTH -----------")
        for k, v in monthsums.items():
            v = f"{v//60:02d}:{v%60:02d}"
            print(f"  {k:7s} {v}")

    def edit(self):
        events = self.getWeek()
        try:
            previousDay = events[0].date.format().split(' ')[0]
        except:
            print("Nothing to show yet...")
            return

        for number, event in enumerate(events):
            if not event.date.format().startswith(previousDay):
                previousDay = event.date.format().split(' ')[0]
                print()
            print(f"{len(events) - number:>2d} {event}")

        while True:
            selected = input("\nSelect> ")
            try:
                selected = len(events) - int(selected)
            except:
                print("No valid number")
                continue
            
            if selected in range(len(events)):
                break
            print("Number not in range")
        oldDate = events[selected].date
        evt = events[selected].edit()
        if evt.date != oldDate:
            # delete old entry and set up new one
            del self.events[oldDate.format()]
        if evt.date != -1:
            self.events[evt.date.format()] = evt
            print(f"   {evt}")
        else:
            print(f"   REMOVED event from {oldDate.format()}")
        self.listview()
        self.write()


    def calculateOvertime(self):
        weekminutes = 0

        overtime = Time.weekstart().shift(minutes=-1)
        try:
            evt = self.events[overtime.format()]
            if evt.type == self.focus and evt.comment == "Wochenübertrag":
                weekminutes -= evt.duration
        except KeyError:
            pass

        for event in self.getWeek():
            if event.type == self.focus:
                weekminutes += event.duration

        for event in self.getDay():
            if event.type == self.focus:
                if event.comment == "Wochenübertrag":
                    weekminutes += event.duration
        
        now = 0
        if self.current and self.current.type == self.focus:
            now += Time.delta(self.current.date, Time.now())

        weekminutes += now
        overtime = self.target - weekminutes
        event = Event(Time.weekend().format(), self.focus, overtime, "Wochenübertrag")
        self.events[event.date.format()] = event
        self.write()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Worktime - a script to keep track of the time spent for specific tasks or activities.", epilog="HEAVY Work in Progress. Written by petrosh. Help+Bugs: <worktime@petrosh.de>")
    parser.add_argument("--config", '-c', default="~/.config/worktime/config.json", help="Configuration file, defaults to ~/.config/worktime/config.json")
    parser.add_argument("--shift", help="format: 'days=-3', 'weeks=5', ...")
    modegroup = parser.add_mutually_exclusive_group()
    modegroup.add_argument("--toggle", '-t', type=str, help="Takes one argument, [CATEGORY] to begin a session or [COMMENT] to end the current session.")
    modegroup.add_argument("--bar", '-b', action='store_true', help="Produces output for a bar like `i3bar`")
    modegroup.add_argument("--interactive", "-i", action="store_true", help="This opens a rofi to choose a category or make a comment to end a session. Wrapper for --toggle")
    modegroup.add_argument("--list", "-l", action="store_true", help="View events of the selected week and summaries of the month and week")
    modegroup.add_argument("--edit", "-e", action="store_true")
    modegroup.add_argument("--overtime", "-o", action="store_true", help="Calculate overtime hours and create event at end of week. CAUTION: currently under construction")
    modegroup.add_argument("--workMonth", "-w", action="store_true", help="Currently, there might be some inaccuracies in the monthly view in `--list` so this is just a bug workaround")
    args = parser.parse_args()

    if args.shift:
        Time.timeshift = {i[0]: int(i[1]) for i in [j.split("=") for j in args.shift.split(",")]}

    cal = Calendar(args.config)
    
    if args.bar:
        cal.bar()
        exit(0)
    
    if args.list:
        cal.listview()
        print()
        cal.calendarview()
        print()
        cal.summaryview()
        exit(0)

    if args.overtime:
        cal.calculateOvertime()
        exit(0)

    if args.workMonth:
        cal.workPerMonth()
        exit(0)

    if args.edit:
        cal.edit()
        exit(0)
    
    if args.interactive:
        try:
            if not cal.current:
                # print different modes
                modestring = " ".join(cal.categories)
                rofi = subprocess.check_output(f"echo {modestring} | tr -s ' ' '\n' | rofi -dmenu -p 'Start timer' -lines {len(cal.categories)}", shell=True, text=True)
                args.toggle = rofi.replace("\n", "")
            else:
                # offer comment input field
                rofi = subprocess.check_output(f"rofi -dmenu -p 'Comment {cal.current.type} session' -lines 0", shell=True, text=True)
                args.toggle = rofi.replace("\n", "")
        except subprocess.CalledProcessError:
            exit(0)

    if args.toggle != None:
        cal.toggle(args.toggle)
