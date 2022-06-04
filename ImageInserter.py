from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run
from os import chdir, getcwd
import sqlite3
from argparse import ArgumentParser
from sys import exit
import logging
from random import choices
from string import ascii_letters, digits


def get_args(optional_arg_string: str = None):
    p = ArgumentParser()
    p.add_argument("database", help="Database file path")
    p.add_argument("gallery", help="path to gallery directory")
    p.add_argument("thumbnail", help="The directory that holds the thumbnails")
    p.add_argument("-v", "--verbose", type=int, choices=[0, 1, 2, 3], default=2,
                   help="Logging level with 3 being the most verbose and \
                       -v 0 being quiet. defaults to 2")
    p.add_argument("--dry-run", action="store_true",
                   help="Run script and show files being inserted without \
            inserting or generating anything.")
    p.add_argument("--log-file", default=None, help="File to store logs to. \
        Logs are appended. Do not specify to log to stdout and stderr.")
    if optional_arg_string is not None:
        return p.parse_args(optional_arg_string.split())
    return p.parse_args()


# _ARGS = get_args(
#     "archive.db mock_archive/images/ mock_archive/thumbnails/ -v 3 --dry-run")
_ARGS = get_args()

LOGGER = logging.getLogger(__name__)
if not _ARGS.dry_run:
    _formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s')
else:
    _formatter = logging.Formatter(
        'DRY-RUN | %(asctime)s | %(levelname)s | %(message)s')
    logging.basicConfig(
        format='DRY-RUN | %(asctime)s | %(levelname)s | %(message)s')

if _ARGS.log_file is not None:
    file_handler = logging.FileHandler(_ARGS.log_file, mode="a")
    file_handler.setFormatter(_formatter)
    LOGGER.addHandler(file_handler)


LOGGER.setLevel([
    "NOTSET",
    "WARNING",
    "INFO",
    "DEBUG"][_ARGS.verbose])

DB_FILE = str(Path(_ARGS.database).resolve())
GALLERY_PATH = Path(_ARGS.gallery).resolve()
THUMBNAIL_DIR_PATH = Path(_ARGS.thumbnail).resolve()

DB_CONN = None
DB_CUR = None
if not _ARGS.dry_run:
    DB_CONN = sqlite3.connect(DB_FILE)
    DB_CUR = DB_CONN.cursor()


INSERT_ARCHIVE_IMAGE_AND_THUMBNAIL = """
INSERT INTO archive (image_path, thumbnail_path) VALUES (?,?)
"""
DOES_THUMBNAIL_EXIST = """
VALUES(EXISTS(SELECT * FROM archive WHERE thumbnail_path = ?))
"""
DOES_IMAGE_EXIST = """
VALUES(EXISTS(SELECT * FROM archive WHERE image_path = ?))
"""


def thumbnail_exists(thumbnail_abs_path):
    """checks for the existence of a thumbnail path

    handles dry-run, returns False

    Args:
        thumbnail_abs_path (str): abs path of thumbnail to check

    Returns:
        bool: True if exists
    """
    if _ARGS.dry_run:
        return False
    _r = DB_CUR.execute(DOES_THUMBNAIL_EXIST, (thumbnail_abs_path,))
    r, *_ = _r.fetchone()
    return r == 1


def image_exists(image_abs_path):
    """Checks for existence of image in db

    Handles dry-run, returns False

    Args:
        image_abs_path (str): abs path of image to check

    Returns:
        bool: True if exists
    """
    if _ARGS.dry_run:
        return False
    _r = DB_CUR.execute(DOES_IMAGE_EXIST, (image_abs_path,))
    r, *_ = _r.fetchone()
    return r == 1


def log_info(msg, *args, **kwargs):
    LOGGER.info(msg, *args, **kwargs)


def log_debug(msg, *args, **kwargs):
    LOGGER.debug(msg, *args, **kwargs)


def log_error(msg, *args, exc_info=None, **kwargs):
    LOGGER.error(msg, *args, exc_info=exc_info, **kwargs)


def create_new_image_record(image_abs_path):
    """Generate a new thumbnail and insert image record into database.

    Handles dry-run

    Args:
        image_abs_path (str): absolute path of image

        thumbnail_abs_path (str): absolute path of thumbnail

    Returns:
        bool: True if success or image already exists
    """
    try:
        if image_exists(image_abs_path):
            log_debug("Image already exists in db: %s", image_abs_path)
            return True

        thumbnail_abs_path = generate_unique_thumbnail_name()

        if not _ARGS.dry_run:
            proc = generate_thumbnail(image_abs_path, thumbnail_abs_path)
            proc.check_returncode()

            DB_CUR.execute(INSERT_ARCHIVE_IMAGE_AND_THUMBNAIL,
                           (image_abs_path, thumbnail_abs_path))

        log_info("%s | %s", image_abs_path, thumbnail_abs_path)
        return True
    except sqlite3.DatabaseError as e:
        log_error("Exception inserting images: %s | %s",
                  image_abs_path, thumbnail_abs_path, exc_info=e)
        return False
    except CalledProcessError as e:
        log_error("Exception occurred when calling OS process: ", exc_info=e)
        return False


def generate_unique_thumbnail_name():
    """Generate unique name for thumbnail that's not in the database.

    dry-run agnostic

    Returns:
        str: unique absolute path name
    """
    def name_gen(): return str(THUMBNAIL_DIR_PATH.resolve() /
                               ("".join(choices(ascii_letters + digits, k=16)) + ".th.jpg"))
    name = name_gen()
    while(thumbnail_exists(name)):
        name = name_gen()
    log_debug("Generated unique name: %s", name)
    return name


def generate_thumbnail(image_abs_path, thumbnail_abs_path):
    """Uses imagemagick to create a thumbnail

    Args:
        image_abs_path (str): absolute path to image

        thumbnail_abs_path (str): absoltue path to thumbnail

    Returns:
        CompletedProcess: of convert, to validate
    """
    input_options = []
    input_file = [image_abs_path]
    output_options = ["-thumbnail", "300x300"]
    output_file = [thumbnail_abs_path]
    cmd = ["convert"] + input_options + \
        input_file + output_options + output_file
    log_debug("Generating thumbnail with: %s", cmd)
    return run(cmd)


def walk_gallery(parent):
    """Walks a directory recursively and inserts an images it finds.

    Args:
        parent (Path): absolute path of a directory
    """
    log_debug("In %s", parent)
    for child in parent.iterdir():
        if child.is_dir():
            walk_gallery(child.resolve())
        else:
            create_new_image_record(str(child.resolve()))


def main():
    log_info("Beginning image insertion")
    current_dir = Path(getcwd()).resolve()
    log_debug("Launched from %s", current_dir)
    chdir(GALLERY_PATH)
    log_debug("Changed directory to %s", GALLERY_PATH)

    walk_gallery(Path(getcwd()).resolve())

    if not _ARGS.dry_run:
        DB_CONN.commit()
        DB_CONN.close()
        log_debug("Committed changes")
    else:
        log_debug("Did not commit changes")

    chdir(current_dir)
    log_debug("Changed directory back to %s", current_dir)
    log_info("Image insertion complete\n")
    exit()


if __name__ == "__main__":
    main()
