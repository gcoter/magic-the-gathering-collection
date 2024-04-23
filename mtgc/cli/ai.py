import os
import json
import random

import pandas as pd


class AICLI:
    def create_dataset(self, deck_folder: str, n_samples_per_deck: int, output_path: str):
        deck_json_dict_list = self.__load_decks(folder_path=deck_folder)
        dataset = self.__create_dataset_from_decks(deck_json_dict_list, n_samples_per_deck=n_samples_per_deck)
        print(f"Saving dataset to '{output_path}'")
        dataset.to_csv(output_path, index=False)

    def __load_decks(self, folder_path: str):
        deck_json_dict_list = []
        deck_filenames = os.listdir(folder_path)
        for filename in deck_filenames:
            path = os.path.join(folder_path, filename)
            deck_json_dict = self.__load_deck(path)
            deck_json_dict_list.append(deck_json_dict)
        return deck_json_dict_list

    def __load_deck(self, path: str):
        with open(path, "r") as f:
            deck_json_dict = json.load(f)
        return deck_json_dict

    def __create_dataset_from_decks(self, deck_json_dict_list, n_samples_per_deck: int):
        dataset = []
        for n, deck_json_dict in enumerate(deck_json_dict_list):
            print(f"Create dataset from deck {n+1}/{len(deck_json_dict_list)}")
            cards = deck_json_dict["cards"]
            for _ in range(n_samples_per_deck // 2):
                # Create one positive pair
                card_1 = random.choice(cards)["name"]
                card_2 = random.choice([card for card in cards if card != card_1])["name"]
                dataset.append({
                    "card_1": card_1,
                    "card_2": card_2,
                    "label": 1
                })

                # Create one negative pair
                other_deck_json_dict = deck_json_dict_list[random.choice([i for i in range(len(deck_json_dict_list)) if i != n])]
                other_deck_cards = other_deck_json_dict["cards"]
                card_2 = random.choice(other_deck_cards)["name"]
                dataset.append({
                    "card_1": card_1,
                    "card_2": card_2,
                    "label": 0
                })

        return pd.DataFrame(dataset)
