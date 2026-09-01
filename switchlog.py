#!/usr/bin/env python3
# 
# switchlog.py
#
# AI logs can grow fast. Large logs slow down DeskChat.
# This program saves the current log "log.md" in a directory called "logs"
# with a date, eg. log082426.zip.
# A new empty current log is created: log.md
# WRITTEN IN 13 SECONDS BY OPENAI (LUNA) USING 168 TOKENS

from pathlib import Path
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
import sys


def main():
    current_log = Path("log.md")
    logs_directory = Path("logs")

    if not current_log.is_file():
        print("Error: log.md does not exist.", file=sys.stderr)
        return 1

    logs_directory.mkdir(exist_ok=True)

    date_string = datetime.now().strftime("%m%d%y")
    archive_path = logs_directory / f"log{date_string}.zip"

    if archive_path.exists():
        print(
            f"Error: archive already exists: {archive_path}",
            file=sys.stderr
        )
        print("The current log was not changed.", file=sys.stderr)
        return 1

    temporary_archive = logs_directory / f".{archive_path.name}.tmp"

    try:
        # Create the ZIP archive.
        with ZipFile(
            temporary_archive,
            mode="w",
            compression=ZIP_DEFLATED
        ) as archive:
            archive.write(current_log, arcname="log.md")

        # Rename the completed temporary archive into place.
        temporary_archive.replace(archive_path)

        # Create a new empty current log.
        current_log.write_text("", encoding="utf-8")

        print(f"Archived log.md as {archive_path}")
        print("Created a new empty log.md")
        return 0

    except Exception as error:
        if temporary_archive.exists():
            temporary_archive.unlink()

        print(f"Error: {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
