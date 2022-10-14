import sys

from twittaloader.__main__ import Twittaloader

if __name__ == "__main__":
    Twittaloader(*sys.argv[1:])()
