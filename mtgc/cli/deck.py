import os
import json
from glob import glob

from mtgc import DEFAULT_FOLDER_PATH


class DeckCLI:
    def __init__(self):
        self.deck_data_folder = os.path.join(DEFAULT_FOLDER_PATH, "decks")
        if not os.path.exists(self.deck_data_folder):
            print(f"Created deck folder at '{self.deck_data_folder}'")
            os.mkdir(self.deck_data_folder)

    def add(
        self,
        deck: str,
        card: str
    ):
        deck_json_dict = self.__get_deck(path=deck)
        card_json_dict_list = self.__get_cards(path_pattern=card)
        deck_json_dict = self.__update_deck(deck_json_dict, card_json_dict_list)
        self.__save_deck(deck_json_dict, path=deck)

    def __get_deck(self, path: str):
        if os.path.exists(path):
            return self.__load_deck(path)

        deck_json_dict = {
            "cards": []
        }
        return deck_json_dict

    def __load_deck(self, path: str):
        with open(path, "r") as f:
            deck_json_dict = json.load(f)
        return deck_json_dict

    def __save_deck(self, deck_json_dict, path: str):
        print(f"Save deck to '{path}'")
        with open(path, "w") as f:
            json.dump(deck_json_dict, f, indent=4)

    def __get_cards(self, path_pattern: str):
        paths = glob(path_pattern)
        card_json_dict_list = []
        for path in paths:
            card_json_dict = self.__load_card(path)
            card_json_dict_list.append(card_json_dict)
        return card_json_dict_list

    def __load_card(self, path):
        with open(path, "r") as f:
            card_json_dict = json.load(f)
        return card_json_dict

    def __update_deck(self, deck_json_dict, card_json_dict_list):
        # FIXME: Treat case where card already exists; for now we reset the list to avoid this
        deck_json_dict["cards"] = []

        print("\n===== Update deck =====")
        for card_json_dict in card_json_dict_list:
            card_name = card_json_dict["scryfall"]["name"]
            max_possible_card_count = card_json_dict["count"]

            print(f"\n***** Add card '{card_name}' *****")
            card_count = max_possible_card_count
            if max_possible_card_count > 1:
                while True:
                    answer = input(f"Enter count (between 1 and {max_possible_card_count}): ")
                    answer = int(answer)
                    if answer >= 1 and answer <= max_possible_card_count:
                        card_count = answer
                        break
            deck_json_dict["cards"].append({
                "name": card_name,
                "count": card_count
            })

        print("\n===== Done updating deck =====\n")
        return deck_json_dict
