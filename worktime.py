#!/usr/bin/env python3



import argparse
import os.path
import arrow
import json
from math import ceil

from os import get_terminal_size

import subprocess

def duration(t1, t2):
    return ceil((t2 - t1).total_seconds() / 60 / 5) * 5

def now():
    return arrow.now().replace(second=0,microsecond=0,tzinfo='+00:00')

def get(cal, stamp):
    return cal[f"{stamp.year:04d}"][f"{stamp.month:02d}"][f"{stamp.day:02d}"]


parser = argparse.ArgumentParser()
parser.add_argument("file")
modegroup = parser.add_mutually_exclusive_group()
modegroup.add_argument("--toggle", '-t')
modegroup.add_argument("--bar", '-b', action='store_true')
modegroup.add_argument("--interactive", "-i", action="store_true")
modegroup.add_argument("--list", "-l", action="store_true")
modegroup.add_argument("--edit", "-e", action="store_true")
args = parser.parse_args()


#calpath = os.path.join(args.folder, "worktime.json")


with open(args.file, 'r') as calfile:
    cal = json.load(calfile)

if args.bar:
    today = now().replace(hour=0,minute=0)
    weekstart = today.shift(weekday=6).shift(days=-6)
    weekminutes = 0
    focus = "work"
    if cal['current'] != []:
        focus = cal['current'][1]
    
    # overtime
    try:
        ov = weekstart.shift(minutes=-1)
        evt = get(cal,ov)
        for time, details in evt.items():
            if time == ov.format("HH:mm") and details[1] < 0 and details[0] == focus:
                weekminutes -= details[1]
    except KeyError:
        pass

    for x in range(7):
        day = weekstart.shift(days=x)
        if day.day == today.day:
            break
        try:
            for time, dur in cal[f"{day.year:04d}"][f"{day.month:02d}"][f"{day.day:02d}"].items():
                if dur[0] == focus:
                    weekminutes += dur[1]
        except KeyError:
            pass
    dayminutes = 0
    try:
        for time, dur in cal[f"{today.year:04d}"][f"{today.month:02d}"][f"{today.day:02d}"].items():
            if dur[0] == focus:
                if dur[1] > 0:
                    dayminutes += dur[1]
                else:
                    weekminutes += dur[1]
    except KeyError:
        pass
    if cal['current'] != [] and cal['current'][1] == focus:
        c = arrow.get(cal['current'][0])
        dayminutes += duration(c, now())
    weekminutes += dayminutes
    targetReached = weekminutes >= cal['target'] and focus == "work"
    weekhours = weekminutes // 60
    weekminutes = weekminutes % 60
    dayhours = dayminutes // 60
    dayminutes = dayminutes % 60
    print(f"[{weekhours:02d}:{weekminutes:02d}|{dayhours:02d}:{dayminutes:02d}]")
    print(f"{dayhours:02d}:{dayminutes:02d}")
    if cal['current'] != [] and cal['current'][1] == focus:
        print("#33AAFF")
    elif targetReached:
        print("#00AA00")
    else:
        print("#AAAAAA")
    exit(0)

elif args.list or args.edit:
    # define important dates
    today = now().replace(hour=0,minute=0)
    monthstart = today.replace(day=1)
    weekstart = today.shift(weekday=6).shift(days=-6)
    weekend = weekstart.shift(days=7,minutes=-1)

    # setup the counters
    monthcount = {cat: 0 for cat in cal['categories']}
    weekcount = {cat: 0 for cat in cal['categories']}

    # overtime
    try:
        ov = weekstart.shift(minutes=-1)
        evt = get(cal,ov)
        for time, details in evt.items():
            if time == ov.format("HH:mm") and details[1] < 0 and details[0] in weekcount:
                weekcount[details[0]] -= details[1]
    except KeyError:
        pass

    # setup the calendar design
    width, height = get_terminal_size()
    height = 48
    daywidth = width // 7 if width%7 >= 3 else (width // 7) - 1
    timewidth = width - 7 * daywidth
    timecolumn = [f"{i//2:02d}:00" + " "*(timewidth-5) if (i/2)%3==0 else " "*timewidth for i in range(height)]
    matrix = [[f' |{"."*(daywidth-4)}| ' for x in range(7)] for y in range(height)]
    earliest = 47
    latest = 0

    c = 0

    for year in cal:
        try: # filter all config stuff
            int(year)
        except ValueError:
            continue
        if int(year) < monthstart.year and int(year) < weekstart.year:
            continue
        for month in cal[year]:
            for day in cal[year][month]:
                eventdate = arrow.get(f"{year}-{month}-{day}")
                if eventdate < monthstart and eventdate < weekstart:
                    continue
                if eventdate >= weekstart:
                    print()
                for time in cal[year][month][day]:
                    event = cal[year][month][day][time]
                    if eventdate >= monthstart:
                        try:
                            if event[1] > 0:
                                monthcount[event[0]] += event[1]
                        except KeyError:
                            pass
                    if eventdate < weekstart or eventdate > weekend:
                        continue
                    try:
                        weekcount[event[0]] += event[1]
                    except KeyError:
                        pass
                    if event[1] < 0:
                        continue
                    if len(event) < 3:
                        event.append("")
                    print(f"{c:2d}| {day}.{month}.{year} {time}> {event[0]:6s} {event[1]:3d} {event[2]}")
                    c += 1
                    ystart = int(time.split(":")[0]) * 2 + (int(time.split(":")[1]) > 30)
                    earliest = min(ystart, earliest)
                    latest = max(latest, ystart+ceil(event[1]/30))
                    inner = daywidth - 6
                    dayoff = 0
                    for i in range(ceil(event[1]/30)):
                        if ystart + i == height:
                            dayoff = 1
                            if dayoff + eventdate.weekday() > 6:
                                break
                        earliest = min(earliest, ystart+i - (dayoff * height))
                        if i >= 1 and event[2] != "" and (i-1) * inner <= len(event[2]):
                            matrix[ystart+i - (dayoff * height)][eventdate.weekday() + dayoff] = \
                                f' | {event[2][(i-1)*inner:min(len(event[2]),i*inner)]:{inner}s} | '
                        else:
                            matrix[ystart+i - (dayoff * height)][eventdate.weekday() + dayoff] = f' |{" "*(daywidth-4)}| '
                    headline = event[0]
                    headline = f" {headline[:min(len(headline),daywidth-6)]} "
                    matrix[ystart][eventdate.weekday()] = f" +{headline:-^{daywidth-4}s}+ "
    
    # current event in calendar view
    if cal['current'] != []:
        cur = arrow.get(cal['current'][0])
        if cur > weekstart and cur < weekend:
            headline = f" {cal['current'][1][:min(len(cal['current'][1]),daywidth-6)]} "
            matrix[cur.hour * 2 + (cur.minute > 30)][cur.weekday()] = f" +{headline:-^{daywidth-4}s}+ "
    
    if args.list:
        print()
        print("WEEK ------------")
        for k, v in weekcount.items():
            v = f"{v//60:02d}:{v%60:02d}"
            print(f"  {k:7s} {v}")
        print()
        print("MONTH -----------")
        for k, v in monthcount.items():
            v = f"{v//60:02d}:{v%60:02d}"
            print(f"  {k:7s} {v}")
        print()


        earliest = int(earliest/6)*6
        latest = ceil(latest/6)*6

        print(" "*(timewidth), end="")
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            print(f"{d:^{daywidth}s}", end="")
        print()
        for row, data in enumerate(zip(matrix,timecolumn)):
            if row < earliest or row > latest:
                continue
            print(data[1], end="")
            for it in data[0]:
                print(it, end="")
            print()
    else:
        edit = input("Edit number: ")

elif args.interactive:

    try:
        if cal['current'] == []:
            # print different modes
            modestring = " ".join(cal["categories"])
            rofi = subprocess.check_output(f"echo {modestring} | tr -s ' ' '\n' | rofi -dmenu -p 'Start timer' -lines {len(cal['categories'])}", shell=True, text=True)
            args.toggle = rofi.replace("\n", "")
        else:
            # offer comment input field
            rofi = subprocess.check_output(f"rofi -dmenu -p 'Comment {cal['current'][1]} session' -lines 0", shell=True, text=True)
            args.toggle = rofi.replace("\n", "")
    except subprocess.CalledProcessError:
        exit(0)


if args.toggle != None:
    if cal['current'] == []:
        x = now()
        cal['current'] = [x.format(), args.toggle]
        if args.toggle == "work":
            subprocess.run("~/bin/wallpapermanager -s", shell=True)
    else:
        c = arrow.get(cal['current'][0])
        y = f"{c.year:04d}"
        m = f"{c.month:02d}"
        d = f"{c.day:02d}"
        if not y in cal:
            cal[y] = dict()
        if not m in cal[y]:
            cal[y][m] = dict()
        if not d in cal[y][m]:
            cal[y][m][d] = dict()
        cal[y][m][d][c.format("HH:mm")] = [cal['current'][1], duration(c, now())]
        if args.toggle != "":
            cal[y][m][d][c.format("HH:mm")].append(args.toggle)
        if cal['current'][1] == "work":
            subprocess.run("~/bin/wallpapermanager -n", shell=True)
        cal['current'] = []
        
    with open(args.file, 'w') as calfile:
        json.dump(cal, calfile)

