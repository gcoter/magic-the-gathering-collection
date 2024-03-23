import os
import json
import requests

from mtgc import DEFAULT_FOLDER_PATH


class CardCLI:
    def __init__(self):
        self.card_data_folder = os.path.join(DEFAULT_FOLDER_PATH, "cards")
        if not os.path.exists(self.card_data_folder):
            print(f"Created card folder at '{self.card_data_folder}'")
            os.mkdir(self.card_data_folder)

    def add(self, query: str):
        card_json_dict = self.__search_for_card(query=query)
        if card_json_dict is None:
            return

        card_path = self.__get_card_path(card_json_dict)
        if os.path.exists(card_path):
            card_json_dict = self.__handle_existing_card(card_json_dict, card_path)
            if card_json_dict is None:
                return

        self.__save_card(card_json_dict, path=card_path)
        card_name = card_json_dict["scryfall"]["name"]
        print(f"Added card '{card_name}' to collection ('{card_path}')")

    def __search_for_card(self, query: str):
        endpoint_url = "https://api.scryfall.com/cards/named"
        params = {"fuzzy": query}

        try:
            response = requests.get(endpoint_url, params=params)
            response.raise_for_status()
            card_scryfall_json_dict = response.json()
            card_json_dict = self.__format_card_json_dict(card_scryfall_json_dict)
            return card_json_dict
        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def __format_card_json_dict(self, card_scryfall_json_dict):
        return {
            "scryfall": card_scryfall_json_dict,
            "count": 1
        }

    def __get_card_path(self, card_json_dict):
        card_filename = self.__get_card_filename(card_json_dict)
        card_path = os.path.join(self.card_data_folder, f"{card_filename}.json")
        return card_path

    def __get_card_filename(self, card_json_dict):
        card_name = card_json_dict["scryfall"]["name"]
        return card_name

    def __handle_existing_card(self, card_json_dict, card_path):
        card_name = card_json_dict["scryfall"]["name"]
        print(f"Card '{card_name}' already exists ('{card_path}')")

        answer = None
        while answer not in ["y", "n"]:
            answer = input("Increment count? (y/n) ").lower()

        if answer == "n":
            return None

        card_json_dict = self.__load_card(path=card_path)
        card_json_dict["count"] += 1
        return card_json_dict

    def __load_card(self, path):
        with open(path, "r") as f:
            card_json_dict = json.load(f)
        return card_json_dict

    def __save_card(self, card_json_dict, path):
        with open(path, "w") as f:
            json.dump(card_json_dict, f, indent=4)
