#!/bin/bash

# Check if any MP3 files are provided
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 file1.mp3 [file2.mp3 ... fileN.mp3]"
    exit 1
fi

# Loop through each provided MP3 file
for input_file in "$@"; do
    # Check if the file has the .mp3 extension
    if [[ "$input_file" == *.mp3 ]]; then
        # Generate output filename by replacing the .mp3 extension with .snd
        output_file="${input_file%.mp3}.snd"

        # Run sox command to convert the file
        if sox "$input_file" -r 16000 -c 1 -b 16 -e signed-integer -t raw "$output_file" vol -30dB dcshift 0.06; then
            echo "Conversion complete: $output_file"
        else
            echo "Failed to convert: $input_file"
        fi
    else
        echo "Skipping non-mp3 file: $input_file"
    fi
done
