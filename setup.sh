#!/bin/bash

cfile="$HOME/.config/worktime/"
mkdir -p "$cfile"
cfile="${cfile}config.json"

read -p 'Name for this worktime session: ' session_name

if [ -f "$cfile" ]; then
    echo -e "\033[0;31mConfig file already exists\033[0m - skipping creation."
    read -p 'Overwrite configuration? [y/N]' anyway
    if [ "$anyway" != "y" ] && [ "$anyway" != "j" ]
    then
        exit
    fi
fi

session_path="$HOME/.local/share/worktime/"

mkdir -p "$session_path"

session_path="${session_path}${session_name}.json"

cat > "$cfile" << EOF
{
  "name": "$session_path",
  "target": {
    "type": "weekly",
    "unit": "h",
    "amount": 0
  },
  "categories": [],
  "focus": ""
}
EOF

echo -e "Created config file in \033[0;32m${cfile}\033[0m"

cat > "$session_path" << EOF
{
  "current": false,
  "events": {}
}
EOF

echo -e "Created save file in \033[0;32m${session_path}\033[0m"
