# Installation

## Dependencies
1. `python3`
2. `rofi` - like `dmenu`, used for interactive mode as simple choice/input GUI.

Just clone the repository.
```
git clone https://github.com/p3tr0sh/worktime.git
```

And then run the `setup.sh` script which will ask for a name to identify this worktime session.
This will create a configuration file and a file to keep track of all events.
```
./setup.sh
```

You might also want to add a link or additional script pointing to the `worktime.py` script to be able to execute this program from arbitrary directories.

# Configuration
`Focus` and `Target` can be configured in the configuration file.
`Focus` points to the default category, used for example in the overtime calculation and bar output for `i3bar` or similar bars.
`Target` is the number of hours (or minutes) to achieve during a month/week. - This feature is still WIP

# Usage

See
```
worktime.py -h
```