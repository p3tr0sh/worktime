#!/usr/bin/env python3



import argparse
import os.path
import json
from math import ceil

from os import get_terminal_size

import subprocess

from timewrapper import Time
from event import Event

class Calendar:

    def __init__(self, filename):
        self.events = dict()
        self.target = -1
        self.categories = []
        self.current = False

        self.filename = filename

        self.read()

    def read(self):
        with open(self.filename, 'r') as calfile:
            cal = json.load(calfile)
            self.target = cal['target']
            self.categories = cal['categories']
            self.current = cal['current']
            if self.current:
                self.current = Event(self.current[0], *self.current[1])
            for date, event in cal['events'].items():
                self.events[date] = Event(date, *event)
    
    def write(self):
        with open(self.filename, 'w') as calfile:
            obj = dict()
            obj['target'] = self.target
            obj['categories'] = self.categories
            if self.current:
                obj['current'] = list(self.current.serialize().items())[0]
            else: 
                obj['current'] = False
            obj['events'] = dict()
            for event in self.events.values():
                obj['events'].update(event.serialize())
            json.dump(obj, calfile, indent=2, ensure_ascii=False)
        

    def getWeek(self):
        weekstart = Time.weekstart()
        weekend   = Time.weekend()
        week = []
        for event in self.events.values():
            if event.date > weekstart and event.date < weekend:
                week.append(event)
        return sorted(week, key=lambda x: x.date.format())
    
    def getMonth(self):
        monthstart = Time.monthstart()
        monthend   = Time.monthend()
        month = []
        for event in self.events.values():
            if event.date > monthstart and event.date < monthend:
                month.append(event)
        return sorted(month, key=lambda x: x.date.format())

    def getOvertime(self, focus="work"):
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
            if option == "work":
                subprocess.run("~/bin/wallpapermanager -s", shell=True)
        else:
            self.current.duration = Time.delta(self.current.date, Time.now())
            self.current.comment = option
            self.events[self.current.date.format()] = self.current
            if self.current.type == "work":
                subprocess.run("~/bin/wallpapermanager -n", shell=True)
            self.current = False
        self.write()

    def bar(self, focus=""):
        if focus == "":
            focus = "work"
            if self.current:
                focus = self.current.type
        weekminutes = 0

        weekminutes -= self.getOvertime()

        for event in self.getWeek():
            if event.type == focus:
                weekminutes += event.duration

        dayminutes = 0

        for event in self.getDay():
            if event.type == focus:
                if event.comment == "Wochenübertrag":
                    weekminutes += event.duration
                else:
                    dayminutes += event.duration
        
        now = 0
        if self.current and self.current.type == focus:
            now += Time.delta(self.current.date, Time.now())

        weekminutes += now
        dayminutes += now
        targetReached = weekminutes >= self.target and focus == "work"
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
        matrix = [[f' |{"."*(daywidth-4)}| ' for x in range(7)] for y in range(height)]
        earliest = 47
        latest = 0

        for event in self.getWeek():
            time = event.date.format().split(" ")[1]
            ystart = int(time.split(":")[0]) * 2 + (int(time.split(":")[1]) > 30)
            earliest = min(ystart, earliest)
            latest = max(latest, ystart+ceil(event.duration/30))
            inner = daywidth - 6
            dayoff = 0
            weekday = event.date.time.weekday()
            for i in range(ceil(event.duration/30)):
                if ystart + i == height:
                    dayoff = 1
                    if dayoff + weekday > 6:
                        break
                earliest = min(earliest, ystart+i - (dayoff * height))
                if i >= 1 and event.comment != "" and (i-1) * inner <= len(event.comment):
                    matrix[ystart+i - (dayoff * height)][weekday + dayoff] = \
                        f' | {event.comment[(i-1)*inner:min(len(event.comment),i*inner)]:{inner}s} | '
                else:
                    matrix[ystart+i - (dayoff * height)][weekday + dayoff] = f' |{" "*(daywidth-4)}| '
            headline = event.type
            headline = f" {headline[:min(len(headline),daywidth-6)]} "
            matrix[ystart][weekday] = f" +{headline:-^{daywidth-4}s}+ "
        
        # current event in calendar view
        if self.current:
            cur = self.current.date
            if cur > Time.weekstart() and cur < Time.weekend():
                headline = f" {self.current.type[:min(len(self.current.type),daywidth-6)]} "
                matrix[cur.time.hour * 2 + (cur.time.minute > 30)][cur.time.weekday()] = f" +{headline:-^{daywidth-4}s}+ "

        earliest = int(earliest/6)*6
        latest = ceil(latest/6)*6

        dates = [Time.weekstart().shift(days=x).format(options="dam") for x in range(7)]
        print(" "*(timewidth), end="")
        for w, d in zip(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], dates):
            if daywidth >= 18:
                header = f" {w} {d}"
            else:
                header = w
            print(f"{header:^{daywidth}s}", end="")
        print()
        for row, data in enumerate(zip(matrix,timecolumn)):
            if row < earliest or row > latest:
                continue
            print(data[1], end="")
            for it in data[0]:
                print(it, end="")
            print()

    def listview(self):
        events = self.getWeek()
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
        week = self.getWeek()
        month = self.getMonth()
        weeksums = {k: sum([x.duration for x in week if x.type == k]) for k in self.categories}
        monthsums = {k: sum([x.duration for x in month if x.type == k]) for k in self.categories}
        weeksums["work"] -= self.getOvertime()
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
            print(f"{len(events) - number: 2d} {event}")

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
            self.events[evt.date.format()] = evt
        print(f"   {evt}")
        self.listview()


    def calculateOvertime(self):
        focus = "work"
        weekminutes = 0

        overtime = Time.weekstart().shift(minutes=-1)
        try:
            evt = self.events[overtime.format()]
            if evt.type == focus and evt.comment == "Wochenübertrag":
                weekminutes -= evt.duration
        except KeyError:
            pass

        for event in self.getWeek():
            if event.type == focus:
                weekminutes += event.duration

        for event in self.getDay():
            if event.type == focus:
                if event.comment == "Wochenübertrag":
                    weekminutes += event.duration
        
        now = 0
        if self.current and self.current.type == focus:
            now += Time.delta(self.current.date, Time.now())

        weekminutes += now
        overtime = self.target - weekminutes
        event = Event(Time.weekend().format(), focus, overtime, "Wochenübertrag")
        self.events[event.date.format()] = event
        self.write()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--shift", help="format: 'days=-3', 'weeks=5', ...")
    modegroup = parser.add_mutually_exclusive_group()
    modegroup.add_argument("--toggle", '-t')
    modegroup.add_argument("--bar", '-b', action='store_true')
    modegroup.add_argument("--interactive", "-i", action="store_true")
    modegroup.add_argument("--list", "-l", action="store_true")
    modegroup.add_argument("--edit", "-e", action="store_true")
    modegroup.add_argument("--overtime", "-o", action="store_true")
    args = parser.parse_args()

    if args.shift:
        Time.timeshift = {i[0]: int(i[1]) for i in [j.split("=") for j in args.shift.split(",")]}

    cal = Calendar(args.file)
    
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
