import os
import json

import pandas as pd


def load_draft_data(draft_data_path: str, draft_data_dtypes_path: str, nrows=None):
    print(f"Load draft data from '{draft_data_path}'")
    with open(draft_data_dtypes_path, "r") as f:
        dtypes_dict = json.load(f)
    draft_data_df = pd.read_csv(draft_data_path, dtype=dtypes_dict, nrows=nrows)
    return draft_data_df


def load_cards_data(card_folder: str):
    print(f"Load card data from '{card_folder}'")
    cards_data_dict = {}
    for filename in os.listdir(card_folder):
        file_path = os.path.join(card_folder, filename)
        card_name = filename.split(".")[0]
        
        with open(file_path, "r") as f:
            card_json_dict = json.load(f)

        cards_data_dict[card_name] = card_json_dict
    return cards_data_dict
