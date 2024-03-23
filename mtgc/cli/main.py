import os
from fire import Fire
from pathlib import Path

from mtgc import DEFAULT_FOLDER_PATH


def init():
    if not os.path.exists(DEFAULT_FOLDER_PATH):
        Path(DEFAULT_FOLDER_PATH).mkdir(parents=True)
        print(f"Created data folder at {DEFAULT_FOLDER_PATH}")


def main():
    Fire({
        "init": init,
    })


if __name__ == "__main__":
    main()
