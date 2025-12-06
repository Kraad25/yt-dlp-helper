# yt-dlp-helper

A simple desktop app to download YouTube videos or audio and edit their metadata using a clean Tkinter GUI.

## Download (Windows)

Download the portable Windows build (no installation needed):

- [yt-dlp-helper v1.0.0 for Windows](https://github.com/Kraad25/yt-dlp-helper/releases/tag/v1.0.0)

Unzip the archive and run `Media-Downloader.exe`.

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
To run from source (macOS/Linux/Windows), FFmpeg and ffprobe must be installed to download and process media.
You can either:

- Install FFmpeg via your OS package manager, or
- Download a static FFmpeg build from [here](https://github.com/yt-dlp/FFmpeg-Builds/wiki/Latest) and place `ffmpeg.exe` and `ffprobe.exe` in a `ffmpeg` folder next to `app.py`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Running

After installing all dependencies and adding ffmpeg's `bin` to your PATH:

From the project root, run:
```bash
python app.py
```

By default, the app looks for FFmpeg in a `ffmpeg` folder next to `app.py`. If you prefer using a global FFmpeg installation instead, ensure it’s on your PATH and remove the `ffmpeg_location` option in `YoutubeModel`.

This will start the Tkinter GUI.