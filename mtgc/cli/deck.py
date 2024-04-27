import os
import re
import json
from glob import glob

import pandas as pd

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

    def stats(self, deck: str, card_folder_path: str):
        deck_json_dict = self.__get_deck(path=deck)
        cards_df = self.__get_card_features_from_deck(deck_json_dict, card_folder_path)
        color_stats = self.__compute_color_stats(cards_df)
        mana_cost_stats = self.__compute_mana_cost_stats(cards_df)
        type_stats = self.__compute_type_stats(cards_df)
        keywords_stats = self.__compute_keywords_stats(cards_df)
        self.__print_report(
            color_stats=color_stats,
            mana_cost_stats=mana_cost_stats,
            type_stats=type_stats,
            keywords_stats=keywords_stats
        )

    def __get_card_features_from_deck(self, deck_json_dict, card_folder_path) -> pd.DataFrame:
        df = []

        for deck_item_dict in deck_json_dict["cards"]:
            card_name = deck_item_dict["name"]
            card_count = deck_item_dict["count"]
            card_path = os.path.join(card_folder_path, f"{card_name}.json")
            with open(card_path, "r") as f:
                card_json_dict = json.load(f)
            df.append({
                **card_json_dict["scryfall"],
                **card_json_dict["17lands"],
                "count": card_count,
            })

        return pd.DataFrame(df)

    def __compute_color_stats(self, cards_df: pd.DataFrame):
        color_stats = {
            "R": 0,
            "W": 0,
            "G": 0,
            "B": 0,
            "U": 0
        }

        for _, color_list in cards_df["color_identity"].items():
            for color in color_list:
                color_stats[color] += 1

        return color_stats

    def __compute_mana_cost_stats(self, cards_df: pd.DataFrame):
        mana_costs = []

        for _, mana_cost_string in cards_df["mana_cost"].items():
            mana_cost = 0
            colorless = re.findall("\d", mana_cost_string)
            if len(colorless) > 0:
                # FIXME: Handle cases like 'Bonecrusher Giant' with two costs
                colorless = int(colorless[0])
            elif len(colorless) == 0:
                colorless = 0
            else:
                raise ValueError()

            mana_cost += colorless
            mana_cost += mana_cost_string.count("{U}")
            mana_cost += mana_cost_string.count("{G}")
            mana_cost += mana_cost_string.count("{B}")
            mana_cost += mana_cost_string.count("{W}")
            mana_cost += mana_cost_string.count("{R}")

            # FIXME: Handle 'X' cost
            if "{X}" in mana_cost_string:
                mana_cost += 1

            mana_costs.append(mana_cost)

        mana_cost_stats = pd.value_counts(mana_costs).sort_index().to_dict()
        return mana_cost_stats

    def __compute_type_stats(self, cards_df: pd.DataFrame):
        type_stats = {}

        for _, type_string in cards_df["type_line"].items():
            type_list = type_string.split(" — ")
            final_type_list = []
            for type_list_item in type_list:
                final_type_list.extend(type_list_item.split(" "))
            final_type_list = set(final_type_list)
            for type_name in final_type_list:
                if type_name not in type_stats:
                    type_stats[type_name] = 0
                type_stats[type_name] += 1

        return type_stats

    def __compute_keywords_stats(self, cards_df: pd.DataFrame):
        keywords_stats = {}

        for _, keyword_list in cards_df["keywords"].items():
            for keyword in keyword_list:
                if keyword not in keywords_stats:
                    keywords_stats[keyword] = 0
                keywords_stats[keyword] += 1

        return keywords_stats

    def __print_report(self, color_stats, mana_cost_stats, type_stats, keywords_stats):
        report = ""

        report += "========== Colors ==========\n\n"

        for color, count in color_stats.items():
            tally = "#" * count
            report += f"{color}\t{tally}\n"

        report += "\n========== Mana Cost ==========\n\n"

        for mana_cost, count in mana_cost_stats.items():
            tally = "#" * count
            report += f"{mana_cost}\t{tally}\n"

        report += "\n========== Types ==========\n\n"

        for type_name, count in type_stats.items():
            tally = "#" * count
            report += f"{type_name}    \t{tally}\n"

        report += "\n========== Keywords ==========\n\n"

        for keyword, count in keywords_stats.items():
            tally = "#" * count
            report += f"{keyword}     \t{tally}\n"

        print(report)
