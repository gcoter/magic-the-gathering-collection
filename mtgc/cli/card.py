import os
import json
import requests

from mtgc import DEFAULT_FOLDER_PATH


class CardCLI:
    def add(self, query: str, card_data_folder: str = os.path.join(DEFAULT_FOLDER_PATH, "cards")):
        card_json_dict = self.__search_for_card(query=query)
        if card_json_dict is None:
            return

        card_path = self.__get_card_path(card_json_dict, card_data_folder=card_data_folder)
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

            # Handle non-English cards
            if card_scryfall_json_dict["lang"] != "en":
                english_card_name = card_scryfall_json_dict["name"]
                return self.__search_for_card(query=english_card_name)

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

    def __get_card_path(self, card_json_dict, card_data_folder):
        card_filename = self.__get_card_filename(card_name=card_json_dict["scryfall"]["name"])
        card_path = os.path.join(card_data_folder, f"{card_filename}.json")
        return card_path

    def __get_card_filename(self, card_name: str):
        card_name = card_name.replace("/", " - ")
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

    def add_from_deck(self, deck: str, output_folder_path: str):
        deck_json_dict = self.__load_deck(deck)
        n_deck_cards = len(deck_json_dict["cards"])
        for n, deck_card_json in enumerate(deck_json_dict["cards"]):
            print(f"Add card {n+1}/{n_deck_cards}")
            card_name = deck_card_json["name"]
            card_filename = self.__get_card_filename(card_name)
            card_path = os.path.join(output_folder_path, f"{card_filename}.json")
            if not os.path.exists(card_path):
                card_json_dict = self.__search_for_card(query=card_name)
                self.__save_card(card_json_dict, path=card_path)
                card_name = card_json_dict["scryfall"]["name"]
                print(f"Added card '{card_name}' to collection ('{card_path}')")

    def __load_deck(self, path):
        with open(path, "r") as f:
            deck_json_dict = json.load(f)
        return deck_json_dict

    def add_from_decks(self, deck_folder: str, output_folder_path: str):
        deck_filenames = os.listdir(deck_folder)
        for n, filename in enumerate(deck_filenames):
            print(f"===== Add cards from deck {n+1}/{len(deck_filenames)} =====")
            deck_file_path = os.path.join(deck_folder, filename)
            self.add_from_deck(deck=deck_file_path, output_folder_path=output_folder_path)

    def add_from_draft_data(self, draft_data_path: str, output_card_folder: str):
        card_names = self.__get_card_names_from_draft_data(draft_data_path)
        for n, card_name in enumerate(card_names):
            print(f"Add card {n+1}/{len(card_names)}")
            self.add(query=card_name, card_data_folder=output_card_folder)

    def __get_card_names_from_draft_data(self, draft_data_path: str):
        with open(draft_data_path, "r") as f:
            header = f.readline().split(",")
        pool_columns = [column.replace("pool_", "") for column in header if column.startswith("pool_")]
        pack_columns = [column.replace("pack_card_", "") for column in header if column.startswith("pack_card_")]
        assert set(pool_columns) == set(pack_columns)
        return pool_columns
