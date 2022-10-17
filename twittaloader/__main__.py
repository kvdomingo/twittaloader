import sys

from .core import Twittaloader


def main():
    tl = Twittaloader(*sys.argv[1:])
    tl()


if __name__ == "__main__":
    main()
