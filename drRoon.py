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

def process_directory(directory, dr_value, metadata_choice):
    success = True
    if metadata_choice != "4":
        success = update_metadata_in_directory(directory, dr_value, metadata_choice)
    return success

def update_metadata_in_directory(directory, dr_value, metadata_choice):
    success = True
    for filename in os.listdir(directory):
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

def update_dr_value(existing_value, dr_value, tag_type):
    dr_text = f"DR {dr_value}"
    separator = '; ' if tag_type == 'ROONALBUMTAG' else ', '
    if not existing_value:
        return dr_text
    existing_parts = [part.strip() for part in existing_value.rstrip(separator).split(separator)]
    existing_dr = next((part for part in existing_parts if part.startswith('DR ')), None)
    if existing_dr == dr_text:
        return None  # No change needed
    new_parts = [part for part in existing_parts if not part.startswith('DR ')] + [dr_text]
    return separator.join(new_parts)

def update_id3_tags(audio, dr_value, metadata_choice):
    updated = False
    if metadata_choice in ["1", "2"]:
        if 'TXXX:VERSION' in audio:
            new_value = update_dr_value(audio['TXXX:VERSION'].text[0], dr_value, 'VERSION')
            if new_value:
                audio['TXXX:VERSION'].text = [new_value]
                updated = True
        else:
            audio.add(TXXX(encoding=3, desc='VERSION', text=f"DR {dr_value}"))
            updated = True
    if metadata_choice in ["1", "3"]:
        if 'TXXX:ROONALBUMTAG' in audio:
            new_value = update_dr_value(audio['TXXX:ROONALBUMTAG'].text[0], dr_value, 'ROONALBUMTAG')
            if new_value:
                audio['TXXX:ROONALBUMTAG'].text = [new_value]
                updated = True
        else:
            audio.add(TXXX(encoding=3, desc='ROONALBUMTAG', text=f"DR {dr_value}"))
            updated = True
    return updated

def update_flac_tags(audio, dr_value, metadata_choice):
    updated = False
    if metadata_choice in ["1", "2"]:
        if 'VERSION' in audio:
            new_value = update_dr_value(audio['VERSION'][0], dr_value, 'VERSION')
            if new_value:
                audio['VERSION'] = [new_value]
                updated = True
        else:
            audio['VERSION'] = [f"DR {dr_value}"]
            updated = True
    if metadata_choice in ["1", "3"]:
        if 'ROONALBUMTAG' in audio:
            new_value = update_dr_value(audio['ROONALBUMTAG'][0], dr_value, 'ROONALBUMTAG')
            if new_value:
                audio['ROONALBUMTAG'] = [new_value]
                updated = True
        else:
            audio['ROONALBUMTAG'] = [f"DR {dr_value}"]
            updated = True
    return updated

def update_mp4_tags(audio, dr_value, metadata_choice):
    updated = False
    if metadata_choice in ["1", "2"]:
        tag = '----:com.apple.iTunes:VERSION'
        if tag in audio:
            new_value = update_dr_value(audio[tag][0].decode('utf-8'), dr_value, 'VERSION')
            if new_value:
                audio[tag] = [new_value.encode('utf-8')]
                updated = True
        else:
            audio[tag] = [f"DR {dr_value}".encode('utf-8')]
            updated = True
    if metadata_choice in ["1", "3"]:
        tag = '----:com.apple.iTunes:ROONALBUMTAG'
        if tag in audio:
            new_value = update_dr_value(audio[tag][0].decode('utf-8'), dr_value, 'ROONALBUMTAG')
            if new_value:
                audio[tag] = [new_value.encode('utf-8')]
                updated = True
        else:
            audio[tag] = [f"DR {dr_value}".encode('utf-8')]
            updated = True
    return updated

def update_dsf_tags(audio, dr_value, metadata_choice):
    updated = False
    if audio.tags is None:
        audio.add_tags()
    id3 = audio.tags
    if metadata_choice in ["1", "2"]:
        if 'TXXX:VERSION' in id3:
            new_value = update_dr_value(id3['TXXX:VERSION'].text[0], dr_value, 'VERSION')
            if new_value:
                id3['TXXX:VERSION'].text = [new_value]
                updated = True
        else:
            id3.add(TXXX(encoding=3, desc='VERSION', text=f"DR {dr_value}"))
            updated = True
    if metadata_choice in ["1", "3"]:
        if 'TXXX:ROONALBUMTAG' in id3:
            new_value = update_dr_value(id3['TXXX:ROONALBUMTAG'].text[0], dr_value, 'ROONALBUMTAG')
            if new_value:
                id3['TXXX:ROONALBUMTAG'].text = [new_value]
                updated = True
        else:
            id3.add(TXXX(encoding=3, desc='ROONALBUMTAG', text=f"DR {dr_value}"))
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
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        if 'foo_dr.txt' in files:
            dr_file_path = os.path.join(root, 'foo_dr.txt')
            dr_value = get_dr_value(dr_file_path)
            if dr_value:
                logger.info(f"Processing directory: {root}")
                success = process_directory(root, dr_value, metadata_choice)
                if success and rename_dr_file_choice == "1":
                    new_dr_file_path = os.path.join(root, 'foo_dr_processed.txt')
                    safe_rename(dr_file_path, new_dr_file_path)
                
                if folder_name_choice == "1":
                    folder_name = os.path.basename(root)
                    current_dr = re.search(r'\(DR (\d+)\)', folder_name)
                    if current_dr:
                        if current_dr.group(1) != dr_value:
                            new_name = re.sub(r'\(DR \d+\)', f'(DR {dr_value})', folder_name)
                            new_path = os.path.join(os.path.dirname(root), new_name)
                            safe_rename(os.path.abspath(root), os.path.abspath(new_path))
                        else:
                            logger.info(f"Folder '{folder_name}' already contains correct DR value. Skipping rename.")
                    else:
                        new_name = f"{folder_name} (DR {dr_value})"
                        new_path = os.path.join(os.path.dirname(root), new_name)
                        safe_rename(os.path.abspath(root), os.path.abspath(new_path))

if __name__ == "__main__":
    main()
