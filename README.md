# drRoon

drRoon is a Python script that automatically tags audio files and albums with Dynamic Range (DR) ratings extracted from foobar2000 dynamic range log files. This tool is particularly useful for music enthusiasts and audiophiles who want to organize and display the more common "crest factor" dynamic range information in their music libraries, as opposed to the R128 method Roon natively uses.  Personally, I wanted to differentiate between different releases of the same album, to see at a glance how compressed a modern remaster might be compared to an original CD, for instance.

## Features

- Recursively processes directories to find `foo_dr.txt` files
- Optionally renames album folders with DR values
- Optionally tags album files with DR values
- Supports MP3, FLAC, M4A (AAC / Apple Lossless), and DSF tagging
- Ability to mark processed folders to avoid re-processing the same albums

## Prerequisites

- Python 3.6 or higher

## Installation

1. Clone this repository or download the script:
   ```
   git clone https://github.com/xportz/drRoon.git
   cd drRoon
   ```

2. Install the required dependencies:
   ```
   pip install mutagen
   ```

## Usage

Run the script from the command line, providing the root directory to process:

```
python drRoon.py /path/to/music/library
```

## Options

When running the script, you'll be prompted with several options:

1. **Album Folder Renaming**
   - Choose whether to add the DR score to the album folder name
   - Example: "2024 - Album Title" → "2024 - Album Title (DR 10)"

2. **Metadata Tagging**
   - Choose how to tag the audio files with DR information:
     - Both VERSION and ROONALBUMTAG tags
     - VERSION tag only
     - ROONALBUMTAG tag only
     - No tagging

3. **Log File Management**
   - Choose whether to rename `foo_dr.txt` to `foo_dr_processed.txt` after successful processing

## Supported File Formats

- MP3
- FLAC
- M4A (AAC)
- DSF

## How It Works

1. The script walks through the specified directory and its subdirectories.
2. It looks for `foo_dr.txt` files, which contain the album DR information.
3. When found, it extracts the DR value and processes the corresponding audio files and/or folder according to the chosen options.
4. Depending on the settings, it can:
   - Rename the album folder to include the DR value
   - Add DR information to the audio file metadata
   - Mark the log file as processed so the album is ignored on future runs of the script

## Notes

- The script uses the `mutagen` library to handle audio file metadata.
- It's recommended to backup your music library before running this script, especially if you choose the folder renaming option.
- It's also recommended to test it on a small subset of your music before running it against your entire music library.  Try copung a few albums to a test folder and run it to see how it operates.
- The script has only been tested on a Mac.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/xportz/drRoon/issues).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
