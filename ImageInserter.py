from pathlib import Path
from subprocess import Popen
from os import chdir

ARCHIVE_ROOT = Path("/")


def generate_thumbnail(image_rel_path, image_basename, destination_folder):

    input_options = []
    input_file = [image_rel_path]
    output_options = ["-thumbnail", "300x300"]
    output_file = [f"{destination_folder}{image_basename}.th.jpg"]
    cmd = input_options + input_file + output_options + output_file
    # validate this popen is working appropriately
    proc = Popen(cmd)


def get_thumbnail_rel_path(image_rel_path): ...


def main():
    chdir(ARCHIVE_ROOT)
