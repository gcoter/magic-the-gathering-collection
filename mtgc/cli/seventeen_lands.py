import os
import json
from glob import glob

import pandas as pd


class SeventeenLandsCLI:
    def __init__(self):
        pass

    def enrich_card(self, card_json_path: str, seventeen_lands_folder: str):
        seventeen_lands_df = self.__load_seventeen_lands_data(seventeen_lands_folder)

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

    def __load_seventeen_lands_data(self, folder_path):
        seventeen_lands_df = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            set_name = filename.split(".")[0]
            df = pd.read_csv(file_path)
            df["Set"] = set_name
            seventeen_lands_df.append(df)
        seventeen_lands_df = pd.concat(seventeen_lands_df).reset_index(drop=True)
        return seventeen_lands_df

    def __get_card_stats(self, card_json_dict, seventeen_lands_df):
        card_set = card_json_dict["scryfall"]["set"]
        card_name = card_json_dict["scryfall"]["name"]
        selector = (seventeen_lands_df["Set"] == card_set) & (seventeen_lands_df["Name"] == card_name)
        if selector.sum() != 1:
            print("Could not find stats")
            return {}
        card_stats = json.loads(seventeen_lands_df[selector].drop(["Name", "Color", "Rarity", "Set"], axis=1).iloc[0].to_json())
        return card_stats

    def __enrich_card_with_stats(self, card_json_dict, card_stats):
        card_json_dict["17lands"] = card_stats
        return card_json_dict

    def __save_enriched_card(self, card_json_dict, path):
        with open(path, "w") as f:
            json.dump(card_json_dict, f, indent=4)
