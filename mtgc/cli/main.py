import os
from fire import Fire
from pathlib import Path

from mtgc import DEFAULT_FOLDER_PATH
from mtgc.cli.card import CardCLI


def init():
    if not os.path.exists(DEFAULT_FOLDER_PATH):
        Path(DEFAULT_FOLDER_PATH).mkdir(parents=True)
        print(f"Created data folder at {DEFAULT_FOLDER_PATH}")


def main():
    Fire({
        "init": init,
        "card": CardCLI(),
    })


if __name__ == "__main__":
    main()
