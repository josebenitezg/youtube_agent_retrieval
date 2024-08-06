#!/bin/bash

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "[Error] OPENAI_API_KEY is not set in the environment."
    echo "Please export OPENAI_API_KEY before running this script."
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "[Error] GOOGLE_API_KEY is not set in the environment."
    echo "Please export GOOGLE_API_KEY before running this script."
    exit 1
fi

# Prompt user for YouTube video ID
echo "[USER] Please enter the YouTube video ID."
echo "Example: For https://www.youtube.com/watch?v=ptHnmgaFvwE, the ID is ptHnmgaFvwE"
read -p "Enter the video ID: " video_id

# Check if video ID is provided
if [ -z "$video_id" ]; then
    echo "Error: No video ID provided."
    exit 1
fi

# Run list_videos.py
echo "[INFO] Running list_videos.py..."
python utils/list_videos.py "$video_id"

# Check if the previous command was successful
if [ $? -ne 0 ]; then
    echo "[Error] list_videos.py failed."
    exit 1
fi

# Run download_captions.py
echo "[INFO] Running download_captions.py..."
python download_captions.py

# Check if the previous command was successful
if [ $? -ne 0 ]; then
    echo "[Error] download_captions.py failed."
    exit 1
fi

# Run ingest.py
echo "Running ingest.py..."
python ingest.py

# Check if the previous command was successful
if [ $? -ne 0 ]; then
    echo "[Error] ingest.py failed."
    exit 1
fi

echo "All operations completed successfully."