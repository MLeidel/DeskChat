#!/bin/env bash

cat << 'EOF'
----------------------------
 Installing Needed software
----------------------------

Execute with: ./aimgui.pyc

EOF

echo "Setting up required packages ..."

pip3 install -r requirements.txt

echo "setting up config ..."

./cmpy aimgui.py
