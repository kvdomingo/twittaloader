import sys

from .core import Twittaloader

if __name__ == "__main__":
    tl = Twittaloader(*sys.argv[1:])
    tl()
