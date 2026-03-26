"""Entry point — delegates to app.server."""
import sys

from app.server import run, Server, Handler, PORT, ROOT, MIME, guess_mime  # re-exported for tests

if __name__ == "__main__":
    run()
