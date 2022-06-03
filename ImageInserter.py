from pathlib import Path
from subprocess import Popen
from os import chdir, getcwd
import sqlite3
from argparse import ArgumentParser
from sys import exit
import logging


def get_args(optional_arg_string: str = None):
    p = ArgumentParser()
    p.add_argument("database", help="Database file path")
    p.add_argument("gallery", help="path to gallery directory")
    p.add_argument("-v", "--verbose", type=int, choices=[0, 1, 2, 3], default=2,
                   help="Logging level with 3 being the most verbose and \
                       -v 0 being quiet. defaults to 2")
    p.add_argument("--dry-run", action="store_true",
                   help="Run script and show files being inserted without \
            inserting or generating anything.")
    if optional_arg_string is not None:
        return p.parse_args(optional_arg_string.split())
    return p.parse_args()


_ARGS = get_args("archive.db mock_archive/images/ -v 3 --dry-run")

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s')
LOGGER.setLevel([
    "NOTSET",
    "WARNING",
    "INFO",
    "DEBUG"][_ARGS.verbose])

DB_FILE = Path(_ARGS.database).resolve()
GALLERY_PATH = Path(_ARGS.gallery).resolve()

DB_CONN = None
DB_CUR = None
if not _ARGS.dry_run:
    DB_CONN = sqlite3.connect(DB_FILE)
    DB_CUR = DB_CONN.cursor()


INSERT_ARCHIVE_IMAGE_AND_THUMBNAIL = """
INSERT INTO archive (image_rel_path, thumbnail_rel_path) VALUES (?,?)
"""


def log_info(msg, *args, **kwargs):
    LOGGER.info(msg, *args, **kwargs)


def log_debug(msg, *args, **kwargs):
    LOGGER.debug(f"\u001b[33m{msg}\u001b[0m", *args, **kwargs)


def log_error(msg, *args, exc_info=None, **kwargs):
    LOGGER.error(f"\u001b[31m{msg}\u001b[0m", *
                 args, exc_info=exc_info, **kwargs)

# TODO finish this function


def generate_thumbnail(image_rel_path, image_basename, destination_folder):

    input_options = []
    input_file = [image_rel_path]
    output_options = ["-thumbnail", "300x300"]
    output_file = [f"{destination_folder}{image_basename}.th.jpg"]
    cmd = input_options + input_file + output_options + output_file
    # validate this popen is working appropriately
    proc = Popen(cmd)


def get_thumbnail_rel_path(image_rel_path): ...


def insert_image(image_rel_path, thumbnail_rel_path):
    try:
        if not _ARGS.dry_run:
            DB_CUR.execute(INSERT_ARCHIVE_IMAGE_AND_THUMBNAIL,
                           (image_rel_path, thumbnail_rel_path))
        log_info("Inserted:\n\t%s\n\t\t%s", image_rel_path, thumbnail_rel_path)
    except Exception as e:
        log_error("Exception inserting images\n\t%s\n\t\t%s",
                  image_rel_path, thumbnail_rel_path, exc_info=e)


def main():
    current_dir = Path(getcwd()).resolve()
    log_debug("Launched from %s", current_dir)
    chdir(GALLERY_PATH)
    log_debug("Changed directory to %s", GALLERY_PATH)

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
