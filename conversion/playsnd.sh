#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <filename.snd>"
    exit 1
fi

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found!"
    exit 2
fi

# Increase volume by a factor of 2 (you can adjust this factor as needed)
sox -t raw -r 16000 -c 1 -b 16 -e signed-integer "$INPUT_FILE" -t pulseaudio vol 10.0

if [ $? -ne 0 ]; then
    echo "Error: Failed to play the file '$INPUT_FILE'"
    exit 3
fi
