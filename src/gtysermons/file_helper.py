from loguru import logger
import os
from abc import ABC, abstractmethod

class FileHelper(ABC):
    def __init__(self):
        self.root_dirname = "John MacArthur - Grace To You Sermon archive -"

    def create_folder(self, val):
        logger.info(f"Creating folder: {val}")
        os.makedirs(f"{val}", exist_ok=True)
        os.chdir(f"{val}")

    def create_root_folder(self):
        self.create_folder(self.root_dirname)

    @abstractmethod
    def filename_correct(self, fn):
        fn = fn.translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\\|`~-=_+\""})
        return f'{fn}.mp3'

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
        logger.info(f"Creating folder: {book_num:02}_{book_name}")
        os.makedirs(f"{book_num:02}_{book_name}", exist_ok=True) #two digits always
        os.chdir(f"{book_num:02}_{book_name}")

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