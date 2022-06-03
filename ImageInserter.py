from pathlib import Path
from subprocess import CalledProcessError, run
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
    if optional_arg_string is not None:
        return p.parse_args(optional_arg_string.split())
    return p.parse_args()


_ARGS = get_args(
    "archive.db mock_archive/images/ mock_archive/thumbnails/ -v 3 --dry-run")
# _ARGS=get_args()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s')
LOGGER.setLevel([
    "NOTSET",
    "WARNING",
    "INFO",
    "DEBUG"][_ARGS.verbose])

DB_FILE = Path(_ARGS.database).resolve()
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


def log_info(msg, *args, **kwargs):
    LOGGER.info(msg, *args, **kwargs)


def log_debug(msg, *args, **kwargs):
    LOGGER.debug(f"\u001b[33m{msg}\u001b[0m", *args, **kwargs)


def log_error(msg, *args, exc_info=None, **kwargs):
    LOGGER.error(f"\u001b[31m{msg}\u001b[0m", *
                 args, exc_info=exc_info, **kwargs)

# TODO finish this function


def generate_thumbnail(image_abs_path, thumbnail_abs_path):
    """Uses imagemagick to create a thumbnail

    handles dry-run

    Args:
        image_abs_path (str): absolute path to image

        thumbnail_abs_path (str): absoltue path to thumbnail

    Returns:
        bool: True if successful
    """
    input_options = []
    input_file = [image_abs_path]
    output_options = ["-thumbnail", "300x300"]
    output_file = [thumbnail_abs_path]
    cmd = input_options + input_file + output_options + output_file
    log_debug("Generating thumbnail with: %s", cmd)

    if not _ARGS.dry_run:
        proc = run(cmd, capture_output=True)
        try:
            proc.check_returncode()
        except CalledProcessError as e:
            log_error(
                "CalledProcessException when generating image thumbnail", exc_info=e)
            return False
        log_debug(proc.stdout)
        log_debug(proc.stderr)

    return True


def generate_unique_thumbnail_name():
    """Generate unique name for thumbnail that's not in the database.

    Handles dry-run

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


def insert_image(image_abs_path, thumbnail_abs_path):
    """Insert image to DB

    Handles dry-run

    Args:
        image_abs_path (str): absolute path of image

        thumbnail_abs_path (str): absolute path of thumbnail

    Returns:
        bool: True if success
    """
    try:
        if not _ARGS.dry_run:
            DB_CUR.execute(INSERT_ARCHIVE_IMAGE_AND_THUMBNAIL,
                           (image_abs_path, thumbnail_abs_path))
        log_info("%s||%s", image_abs_path, thumbnail_abs_path)
        return True
    except Exception as e:
        log_error("Exception inserting images: ",
                  image_abs_path, thumbnail_abs_path, exc_info=e)
        return False


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
            _child_abs = child.resolve()
            _child_abs_thumbnail = generate_unique_thumbnail_name()
            if not generate_thumbnail(str(_child_abs), str(_child_abs_thumbnail)):
                continue
            insert_image(str(_child_abs), str(_child_abs_thumbnail))


def main():
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
    exit()


if __name__ == "__main__":
    main()
