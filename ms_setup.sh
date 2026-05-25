#!/bin/env bash

cat << 'EOF'
-----------------------------
 Needed software for DeskChat
-----------------------------

Debian Linux
sudo apt install python3-pip python3-tk
sudo apt install -y libffi-dev
sudo apt install -y libjpeg-dev zlib1g-dev
sudo apt install -y build-essential python3-dev
sudo apt install -y python3-pil.imagetk

Arch
sudo pacman -S tk
sudo pacman -S pip

pip3 install -r requirements.txt
EOF

echo __________________________________
echo Begin installing needed packages
echo ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

sudo apt install python3-pip python3-tk
sudo apt install -y libffi-dev
sudo apt install -y libjpeg-dev zlib1g-dev
sudo apt install -y build-essential python3-dev
sudo apt install -y python3-pil.imagetk

pip3 install -r requirements.txt --break-system-packages

cat << 'EOF'
__________________________________
You will need to set up environmant
keys to use the various AI API
modules. You can do that at the
AI company\'s website.

To use Ollama\'s local models download
the llama app from their website
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
EOF
