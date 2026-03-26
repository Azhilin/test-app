"""Entry point — delegates to app.cli."""
import sys

from app.cli import main, _parse_args, _timestamp_folder_name  # re-exported for tests

if __name__ == "__main__":
    sys.exit(main())
