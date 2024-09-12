import os
import shutil
import re
import logging
import argparse
from mutagen.id3 import ID3, TXXX
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.dsf import DSF
from mutagen import MutagenError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_rename(old_path, new_path):
    if os.path.exists(new_path):
        base, extension = os.path.splitext(new_path)
        counter = 1
        while os.path.exists(f"{base}_{counter}{extension}"):
            counter += 1
        new_path = f"{base}_{counter}{extension}"
    
    try:
        shutil.move(old_path, new_path)
        logger.info(f"Renamed '{old_path}' to '{new_path}'")
    except OSError as e:
        logger.error(f"Error renaming '{old_path}' to '{new_path}': {str(e)}")

def get_dr_value(dr_file_path):
    try:
        with open(dr_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'Official DR value: DR(\d+)', content)
            if match:
                return match.group(1)
            else:
                logger.warning(f"No DR value found in {dr_file_path}")
                return None
    except FileNotFoundError:
        logger.warning(f"{dr_file_path} not found")
        return None
    except IOError as e:
        logger.error(f"Error reading {dr_file_path}: {str(e)}")
        return None

def process_directory(directory, dr_value, folder_name_choice, metadata_choice):
    success = True
    # Update folder name if chosen and DR value not already present
    if folder_name_choice == "1":
        folder_name = os.path.basename(directory)
        if not re.search(r'\(DR \d+\)', folder_name):
            new_name = f"{folder_name} (DR {dr_value})"
            if new_name != folder_name:
                new_path = os.path.join(os.path.dirname(directory), new_name)
                safe_rename(os.path.abspath(directory), os.path.abspath(new_path))
                directory = new_path  # Update directory path for metadata update
        else:
            logger.info(f"Folder '{folder_name}' already contains DR value. Skipping rename.")

    # Update metadata if chosen
    if metadata_choice != "4":
        success = update_metadata_in_directory(directory, dr_value, metadata_choice)

    return success, directory

def update_metadata_in_directory(directory, dr_value, metadata_choice):
    success = True
    for filename in os.listdir(directory):
        # Skip files starting with a period without logging
        if filename.startswith('.'):
            continue
        
        filepath = os.path.join(directory, filename)
        try:
            if filepath.lower().endswith(('.mp3', '.flac', '.m4a', '.dsf')):
                if filepath.lower().endswith('.mp3'):
                    audio = ID3(filepath)
                    updated = update_id3_tags(audio, dr_value, metadata_choice)
                elif filepath.lower().endswith('.flac'):
                    audio = FLAC(filepath)
                    updated = update_flac_tags(audio, dr_value, metadata_choice)
                elif filepath.lower().endswith('.m4a'):
                    audio = MP4(filepath)
                    updated = update_mp4_tags(audio, dr_value, metadata_choice)
                elif filepath.lower().endswith('.dsf'):
                    audio = DSF(filepath)
                    updated = update_dsf_tags(audio, dr_value, metadata_choice)

                if updated:
                    audio.save()
                    logger.info(f"Updated metadata for {filename}")
                else:
                    logger.info(f"No changes needed for {filename}")
            else:
                logger.debug(f"Skipped unsupported file type: {filename}")
        except MutagenError as e:
            logger.error(f"Error updating metadata for {filename}: {str(e)}")
            success = False
        except IOError as e:
            logger.error(f"Error reading/writing file {filename}: {str(e)}")
            success = False
    return success

def update_id3_tags(audio, dr_value, metadata_choice):
    updated = False
    dr_text = f"DR {dr_value}"
    if metadata_choice in ["1", "2"]:
        if 'TXXX:VERSION' not in audio or audio['TXXX:VERSION'].text[0] != dr_text:
            audio.add(TXXX(encoding=3, desc='VERSION', text=dr_text))
            updated = True
    if metadata_choice in ["1", "3"]:
        if 'TXXX:ROONALBUMTAG' not in audio or audio['TXXX:ROONALBUMTAG'].text[0] != dr_text:
            audio.add(TXXX(encoding=3, desc='ROONALBUMTAG', text=dr_text))
            updated = True
    return updated

def update_flac_tags(audio, dr_value, metadata_choice):
    updated = False
    dr_text = f"DR {dr_value}"
    if metadata_choice in ["1", "2"]:
        if 'VERSION' not in audio or audio['VERSION'][0] != dr_text:
            audio['VERSION'] = dr_text
            updated = True
    if metadata_choice in ["1", "3"]:
        if 'ROONALBUMTAG' not in audio or audio['ROONALBUMTAG'][0] != dr_text:
            audio['ROONALBUMTAG'] = dr_text
            updated = True
    return updated

def update_mp4_tags(audio, dr_value, metadata_choice):
    updated = False
    dr_text = f"DR {dr_value}".encode('utf-8')
    if metadata_choice in ["1", "2"]:
        if '----:com.apple.iTunes:VERSION' not in audio or audio['----:com.apple.iTunes:VERSION'][0] != dr_text:
            audio['----:com.apple.iTunes:VERSION'] = [dr_text]
            updated = True
    if metadata_choice in ["1", "3"]:
        if '----:com.apple.iTunes:ROONALBUMTAG' not in audio or audio['----:com.apple.iTunes:ROONALBUMTAG'][0] != dr_text:
            audio['----:com.apple.iTunes:ROONALBUMTAG'] = [dr_text]
            updated = True
    return updated

def update_dsf_tags(audio, dr_value, metadata_choice):
    updated = False
    dr_text = f"DR {dr_value}"
    
    # Ensure the DSF file has an ID3 tag
    if audio.tags is None:
        audio.add_tags()
    
    id3 = audio.tags
    
    if metadata_choice in ["1", "2"]:
        if 'TXXX:VERSION' not in id3 or id3['TXXX:VERSION'].text[0] != dr_text:
            id3.add(TXXX(encoding=3, desc='VERSION', text=dr_text))
            updated = True
    if metadata_choice in ["1", "3"]:
        if 'TXXX:ROONALBUMTAG' not in id3 or id3['TXXX:ROONALBUMTAG'].text[0] != dr_text:
            id3.add(TXXX(encoding=3, desc='ROONALBUMTAG', text=dr_text))
            updated = True
    return updated

def main():
    parser = argparse.ArgumentParser(description="Process DR values in audio files and directories.")
    parser.add_argument("root_dir", help="Root directory to process")
    args = parser.parse_args()

    root_dir = args.root_dir

    if not os.path.isdir(root_dir):
        logger.error(f"The specified directory '{root_dir}' does not exist.")
        return

    print("Would you like to add the DR score to the album folder name?")
    print("1. Yes")
    print("2. No (default)")
    folder_name_choice = input("Enter your choice (1 or 2): ").strip() or "2"

    print("Would you like to add the DR score to metadata?")
    print("1. Yes, to both the VERSION and ROONALBUMTAG tags (default)")
    print("2. Yes, to the VERSION tag only")
    print("3. Yes, to the ROONALBUMTAG tag only")
    print("4. No")
    metadata_choice = input("Enter your choice (1, 2, 3, or 4): ").strip() or "1"

    print("Would you like to rename foo_dr.txt to foo_dr_processed.txt after successful processing?")
    print("1. Yes (default)")
    print("2. No")
    rename_dr_file_choice = input("Enter your choice (1 or 2): ").strip() or "1"

    for root, dirs, files in os.walk(root_dir):
        # Remove hidden directories from the dirs list
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        if 'foo_dr.txt' in files:
            dr_file_path = os.path.join(root, 'foo_dr.txt')
            dr_value = get_dr_value(dr_file_path)
            if dr_value:
                logger.info(f"Processing directory: {root}")
                success, new_dir = process_directory(root, dr_value, folder_name_choice, metadata_choice)
                if success and rename_dr_file_choice == "1":
                    new_dr_file_path = os.path.join(new_dir, 'foo_dr_processed.txt')
                    safe_rename(dr_file_path, new_dr_file_path)

if __name__ == "__main__":
    main()