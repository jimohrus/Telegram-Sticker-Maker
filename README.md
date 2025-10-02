# telegram-sticker-maker

This Python application converts GIF files into WebM format suitable for Telegram video stickers. It ensures the output meets Telegram's requirements: 512x512 pixels, maximum file size of 256 KB, 30 FPS, and a maximum duration of 3 seconds, using VP9 encoding with alpha channel support for transparency.
Features

Converts GIF animations to WebM video stickers.
Automatically crops transparent borders and resizes frames to 512x512 pixels.
Enforces Telegram's 256 KB file size limit through iterative compression (CRF and bitrate adjustments).
Supports a fixed 30 FPS and ensures duration does not exceed 3 seconds.
User-friendly Tkinter GUI for selecting input GIF and output WebM paths.

Prerequisites

Python 3.x: Ensure Python 3.6 or higher is installed.
FFmpeg: Required for video conversion. Download from ffmpeg.org or install via a package manager (e.g., choco install ffmpeg on Windows, sudo apt install ffmpeg on Ubuntu).
Add FFmpeg to your system's PATH environment variable.


Python Libraries: Install required libraries listed in requirements.txt.

Installation

Clone or download this repository to your local machine.
Install the required Python libraries:pip install -r requirements.txt


Ensure FFmpeg is installed and accessible in your system's PATH:
On Windows, run ffmpeg -version in a command prompt to verify.
On Linux/macOS, use ffmpeg -version in a terminal.



Usage

Run the script:python webm_animated_sticker_maker_telegram.py


The GUI will open:
Click "Browse" next to "Select Input GIF" to choose a GIF file.
Click "Browse" next to "Save WebM As" to specify the output WebM file path.
Click "Convert" to process the GIF and generate a Telegram-compliant WebM sticker.


Monitor the status label for progress updates (e.g., "Processing frames...", "Conversion complete!").
If the output exceeds 256 KB, the script will retry with higher compression and display a warning if the limit cannot be met.

Notes

The input GIF should have transparency (alpha channel) for best results, as Telegram video
