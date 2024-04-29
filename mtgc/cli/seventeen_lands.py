import os
import json
from glob import glob

import pandas as pd


class SeventeenLandsCLI:
    def __init__(self):
        pass

    def enrich_card(self, card_json_path: str, seventeen_lands_stats_path: str):
        seventeen_lands_df = self.__load_seventeen_lands_data(seventeen_lands_stats_path)

        for path in glob(card_json_path):
            print(f"===== Enrich '{path}' =====")
            card_json_dict = self.__load_card(path)
            card_stats = self.__get_card_stats(card_json_dict, seventeen_lands_df)
            card_json_dict = self.__enrich_card_with_stats(card_json_dict, card_stats)
            self.__save_enriched_card(card_json_dict, path=path)

    def __load_card(self, path: str):
        with open(path, "r") as f:
            card_json_dict = json.load(f)
        return card_json_dict

    def __load_seventeen_lands_data(self, seventeen_lands_stats_path: str):
        seventeen_lands_df = pd.read_csv(seventeen_lands_stats_path)
        return seventeen_lands_df

    def __get_card_stats(self, card_json_dict, seventeen_lands_df):
        card_name = card_json_dict["scryfall"]["name"]
        selector = seventeen_lands_df["Name"] == card_name
        if selector.sum() == 0:
            print("Could not find stats")
            return {}
        if selector.sum() > 1:
            raise ValueError("Several instances of the same card were found in 17lands stats")
        card_stats = json.loads(seventeen_lands_df[selector].drop(["Name", "Color", "Rarity"], axis=1).iloc[0].to_json())

        for card_stat_name, card_stat_value in card_stats.items():
            if isinstance(card_stat_value, str) and "%" in card_stat_value:
                card_stats[card_stat_name] = float(card_stat_value.replace("%", ""))
            if isinstance(card_stat_value, str) and "pp" in card_stat_value:
                card_stats[card_stat_name] = float(card_stat_value.replace("pp", ""))
        return card_stats

    def __enrich_card_with_stats(self, card_json_dict, card_stats):
        card_json_dict["17lands"] = card_stats
        return card_json_dict

    def __save_enriched_card(self, card_json_dict, path):
        with open(path, "w") as f:
            json.dump(card_json_dict, f, indent=4)

    def create_draft_data_schema(self, draft_data_path: str, output_path: str):
        dtypes_dict = self.__create_draft_data_dtypes(draft_data_path)
        with open(output_path, "w") as f:
            json.dump(dtypes_dict, f, indent=4)

    def __create_draft_data_dtypes(self, draft_data_path: str):
        df = pd.read_csv(draft_data_path, nrows=1)
        dtypes_dict = {
            "expansion": "str",
            "event_type": "str",
            "draft_id": "str",
            "draft_time": "str",
            "rank": "str",
            "event_match_wins": "uint8",
            "event_match_losses": "uint8",
            "pack_number": "uint8",
            "pick_number": "uint8",
            "pick": "str",
            "pick_maindeck_rate": "float16",
            "pick_sideboard_in_rate": "float16",
            "user_n_games_bucket": "uint16",
            "user_game_win_rate_bucket": "float32"
        }

        for column in df.columns:
            if column not in dtypes_dict:
                if column.startswith("pack_card_") or column.startswith("pool_"):
                    dtypes_dict[column] = "uint8"
                else:
                    raise ValueError(f"Unexpected column '{column}'")

        return dtypes_dict
