# yt-dlp-helper

A simple desktop app to download YouTube videos or audio and edit their metadata using a clean Tkinter GUI.

## Features

- Uses `yt-dlp` under the hood
- Download from YouTube as:
  - MP3 (audio only)
  - MP4 (video)
- Quality selection (e.g. 360p, 720p, 1080p, etc.)
- Optional metadata presets:
  - Artist
  - Album
- Step‑by‑step metadata editor for downloaded files:
  - View each file’s current title
  - Edit and save metadata
  - Rename files using:
    - `Title - Artist`
    - `Title - Album`
    - `Title`

## Prerequisites
FFmpeg and ffprobe must be installed to download and process videos.  
Download a Windows build from [here](https://github.com/yt-dlp/FFmpeg-Builds/wiki/Latest) or install via your OS package manager.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Running

After installing all dependencies and adding FFmpeg/ffprobe to your PATH:

From the project root, run:
```bash
python app.py
```

This will start the Tkinter GUI.

