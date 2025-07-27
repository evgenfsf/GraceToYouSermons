from loguru import logger
import os
from abc import ABC, abstractmethod

# --- Utility ---
INVALID_CHARS = {ord(c): "_" for c in r"!@#$%^&*()[]{};:,./<>?\\|`~-=_+\""}

def enforce_path_limit(directory, raw_filename, ext=".mp3", max_path_len=250):
    """
    Truncate filename if full path is too long.
    - Strips invalid chars
    - Removes code if needed
    - Trims title from end
    """
    # Clean filename
    raw_filename = raw_filename.translate(INVALID_CHARS).strip()
    filename = f"{raw_filename}{ext}"
    full_path = os.path.abspath(os.path.join(directory, filename))
    logger.info(f"Full path filename: {full_path}")
    logger.info(f"Full path length:  {len(full_path)}")

    if len(full_path) <= max_path_len:
        return filename

    # Remove code (assumed last part after last "_")
    parts = raw_filename.split("_")
    if len(parts) > 1:
        raw_filename = "_".join(parts[:-1])
        filename = f"{raw_filename}{ext}"
        full_path = os.path.abspath(os.path.join(directory, filename))
        logger.info(f"New full path filename: {full_path}")
        if len(full_path) <= max_path_len:
            return filename

    # Still too long? Trim characters from the end
    excess = len(full_path) - max_path_len
    trimmed = raw_filename[:-excess].rstrip("_")
    filename = f"{trimmed}{ext}"
    logger.info(f"Trimmed filename: {filename}")
    return filename

# --- File Helper Base and Subclasses ---

class FileHelper(ABC):
    def __init__(self):
        self.root_dirname = "John MacArthur - Grace To You Sermon archive -"

    def create_folder(self, val):
        logger.info(f"Creating folder: {val}")
        os.makedirs(f"{val}", exist_ok=True)
        os.chdir(f"{val}")

    def create_root_folder(self):
        self.create_folder(self.root_dirname)

    def filename_correct(self, raw_filename):
        directory = os.getcwd()
        return enforce_path_limit(directory, raw_filename)

class DateFileHelper(FileHelper):
    def __init__(self):
        super().__init__()
        self.root_dirname = f"{self.root_dirname} By Date"

    def filename_correct(self, scripture, title, date, code):
        fn = f"{date}_{title}_{scripture}_{code}"
        return super().filename_correct(fn)

class ScriptureFileHelper(FileHelper):
    def __init__(self):
        super().__init__()
        self.root_dirname = f"{self.root_dirname} By Scripture"

    def create_folder(self, book_num, book_name):
        folder_name = f"{book_num:02}_{book_name}"
        logger.info(f"Creating folder: {folder_name}")
        os.makedirs(folder_name, exist_ok=True)
        os.chdir(folder_name)

    def filename_correct(self, scripture, title, date, code):
        fn = f"{scripture}_{title}_{date}_{code}"
        return super().filename_correct(fn)

class TitleFileHelper(FileHelper):
    def __init__(self):
        super().__init__()
        self.root_dirname = f"{self.root_dirname} By Title"    

    def filename_correct(self, scripture, title, date, code):
        fn = f"{title}_{scripture}_{date}_{code}"
        return super().filename_correct(fn)
